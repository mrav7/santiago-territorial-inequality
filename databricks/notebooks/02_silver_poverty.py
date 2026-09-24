# Databricks notebook source
# MAGIC %md
# MAGIC # 02 · Silver — Poverty by income (Source C)
# MAGIC
# MAGIC `workspace.bronze.pobreza_ingresos` → commune-row classification → `codigo_comuna` → join with the master dimension
# MAGIC → proportion × 100 → `workspace.silver.pobreza_ingresos` (Delta).
# MAGIC
# MAGIC Contract: P04 as corrected by C04-A (year fixture, 4–5 digit code rule) and resumed by C04-C.
# MAGIC
# MAGIC - Final grain: one row per commune of the Provincia de Santiago (32), resolved by `codigo_comuna` against `dim_comuna_base.csv`.
# MAGIC - Silver columns: `codigo_comuna INT`, `nombre_comuna STRING`, `pobreza_ingresos_pct DECIMAL(7,4)`, `anio_pobreza INT`.
# MAGIC - All Data Quality (DQ-S01…S22) and baseline equivalence (EQ-S01…S10) checks run **before** the write. A failed check raises and stops the run.
# MAGIC - Snapshot overwrite of a managed Delta table. This is not incremental processing and not `MERGE`.
# MAGIC
# MAGIC Run on serverless notebook compute. Nothing is installed.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Configuration

# COMMAND ----------

import hashlib
import os
import sys
from decimal import Decimal

from pyspark.sql import functions as F

BRONZE_TABLE = "workspace.bronze.pobreza_ingresos"
TARGET_TABLE = "workspace.silver.pobreza_ingresos"

VOLUME_ROOT = "/Volumes/workspace/bronze/source_files"
DIM_PATH = f"{VOLUME_ROOT}/dim_comuna_base.csv"
STAGING_FIXTURE_PATH = f"{VOLUME_ROOT}/validation_baselines/pobreza_staging.csv"
PROCESSED_FIXTURE_PATH = f"{VOLUME_ROOT}/validation_baselines/desigualdad_comunal_final.csv"

# Identity of the versioned repository files, measured locally before upload.
EXPECTED_FILES = {
    DIM_PATH: (1779, "c8e831949b07bbefed64ffd0e50ee73937c657bbb5071b3741007b9e73532aad"),
    STAGING_FIXTURE_PATH: (801, "df30cab6ee700c1a91237accabbc16085823a14d38cb62a38fea64b2879b3c14"),
    PROCESSED_FIXTURE_PATH: (3034, "66f481a82cf74d108507c9feaf83bc280ab3420e90d2dae7dbb74817897d98a4"),
}

# Bronze contract validated in P03.
EXPECTED_BRONZE_ROWS = 351
EXPECTED_BRONZE_COLUMNS = [
    "codigo",
    "region",
    "nombre_comuna",
    "numero_de_personas_segun_proyecciones_de_poblacion",
    "numero_de_personas_en_situacion_de_pobreza_por_ingresos",
    "porcentaje_de_personas_en_situacion_de_pobreza_por_ingresos_2022",
    "limite_inferior",
    "limite_superior",
    "presencia_de_la_comuna_en_la_muestra_casen",
    "tipo_de_estimacion_sae",
    "_source_dataset",
    "_source_file",
    "_source_path",
    "_source_year",
    "_ingested_at_utc",
]
EXPECTED_BRONZE_VERSIONS = [0, 1]
POVERTY_SOURCE_COLUMN = "porcentaje_de_personas_en_situacion_de_pobreza_por_ingresos_2022"
SOURCE_YEAR = 2022

# Commune-row rule (C04-A, B2 resolved with Databricks evidence): the source uses CUT codes
# without a leading zero, so valid commune codes have 4 or 5 digits.
COMMUNE_CODE_REGEX = "^[0-9]{4,5}$"
EXPECTED_VALID_COMMUNE_ROWS = 345
EXPECTED_NON_COMMUNE_ROWS = 6  # 1 empty row + 5 methodological notes (B2-A/B2-B)
EXPECTED_MASTER_KEYS = 32

EXPECTED_SILVER_SCHEMA = [
    ("codigo_comuna", "int"),
    ("nombre_comuna", "string"),
    ("pobreza_ingresos_pct", "decimal(7,4)"),
    ("anio_pobreza", "int"),
]

# The local pipeline rounds to 4 decimals; values are compared after that rounding.
EQUIVALENCE_TOLERANCE = 1e-9

# P04 §27: the first run must not find an existing Silver table. Set to True only for a
# documented rerun after a real correction (P04 §47).
ALLOW_EXISTING_TARGET = False

dq_results = []


def check(check_id, description, passed, detail=""):
    """Record a check and stop the run if it fails."""
    status = "PASS" if passed else "FAIL"
    dq_results.append((check_id, description, status, str(detail)))
    print(f"[{status}] {check_id} {description} :: {detail}")
    if not passed:
        raise AssertionError(f"{check_id} failed: {description} :: {detail}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Runtime and target pre-check

# COMMAND ----------

print("Python:", sys.version)
print("Spark:", spark.version)

spark_action_count = spark.range(1).count()
print("spark.range(1).count() =", spark_action_count)
assert spark_action_count == 1, "Spark action returned an unexpected result"

target_existed_before = spark.catalog.tableExists(TARGET_TABLE)
print("Silver target existed before this run:", target_existed_before)
if target_existed_before and not ALLOW_EXISTING_TARGET:
    raise RuntimeError(
        f"BLOCKED: {TARGET_TABLE} already exists. Investigate who created it before any write "
        "(P04 §27). Do not drop it."
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Bronze contract (input)

# COMMAND ----------

bronze_exists = spark.catalog.tableExists(BRONZE_TABLE)
bronze_format = spark.sql(f"DESCRIBE DETAIL {BRONZE_TABLE}").first()["format"] if bronze_exists else None
check("DQ-S01", "Bronze table exists and is Delta", bronze_exists and bronze_format == "delta", f"{BRONZE_TABLE} format={bronze_format}")

bronze_df = spark.table(BRONZE_TABLE)
bronze_count = bronze_df.count()
check("DQ-S02", "Bronze row count", bronze_count == EXPECTED_BRONZE_ROWS, bronze_count)

bronze_history = (
    spark.sql(f"DESCRIBE HISTORY {BRONZE_TABLE}")
    .select("version", "operation", F.col("operationMetrics")["numOutputRows"].alias("numOutputRows"))
    .orderBy("version")
)
bronze_history.show(truncate=False)
bronze_versions = [row["version"] for row in bronze_history.collect()]

bronze_meta = bronze_df.agg(
    F.collect_set("_source_dataset").alias("datasets"),
    F.collect_set("_source_file").alias("files"),
    F.collect_set("_source_year").alias("years"),
    F.countDistinct("_ingested_at_utc").alias("snapshots"),
).first()
poverty_type = bronze_df.schema[POVERTY_SOURCE_COLUMN].dataType.simpleString()
print("Bronze metadata:", bronze_meta.asDict())
print("Bronze poverty column type:", poverty_type)

bronze_contract_ok = (
    bronze_df.columns == EXPECTED_BRONZE_COLUMNS
    and bronze_meta["datasets"] == ["pobreza_ingresos"]
    and bronze_meta["files"] == ["estimaciones_tasa_pobreza_ingresos_comunas_2022.xlsx"]
    and bronze_meta["years"] == [SOURCE_YEAR]
    and bronze_meta["snapshots"] == 1
    and bronze_versions == EXPECTED_BRONZE_VERSIONS
    # Exact decimal arithmetic is what makes the × 100 + rounding reproducible (R04 §8).
    and poverty_type.startswith("decimal")
)
check(
    "DQ-S03",
    "Bronze required contract (columns, metadata, single snapshot, P03 history, decimal poverty)",
    bronze_contract_ok,
    f"columns={len(bronze_df.columns)} versions={bronze_versions} poverty_type={poverty_type}",
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Auxiliary file integrity
# MAGIC
# MAGIC The master dimension and the two validation fixtures must be byte-identical to the versioned repository files.

# COMMAND ----------


def file_identity(path):
    with open(path, "rb") as handle:
        return os.path.getsize(path), hashlib.sha256(handle.read()).hexdigest()


remote_identity = {}
for path in EXPECTED_FILES:
    remote_identity[path] = file_identity(path) if os.path.isfile(path) else None
    print(f"{path}\n  remote  : {remote_identity[path]}\n  expected: {EXPECTED_FILES[path]}")

check("DQ-S04", "master dimension file size + SHA-256 = repository", remote_identity[DIM_PATH] == EXPECTED_FILES[DIM_PATH], remote_identity[DIM_PATH])
check(
    "DQ-S05",
    "validation fixtures size + SHA-256 = repository (staging + processed)",
    all(remote_identity[p] == EXPECTED_FILES[p] for p in (STAGING_FIXTURE_PATH, PROCESSED_FIXTURE_PATH)),
    {p: remote_identity[p] for p in (STAGING_FIXTURE_PATH, PROCESSED_FIXTURE_PATH)},
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Master commune dimension
# MAGIC
# MAGIC Read as text (no schema inference), then cast explicitly. Only the key and the canonical name are needed.
# MAGIC The dimension is used as a filtering/validation contract and is not persisted in P04.

# COMMAND ----------

dim_raw_df = spark.read.option("header", True).option("encoding", "UTF-8").csv(DIM_PATH)
dim_raw_df.printSchema()

dim_df = dim_raw_df.select(
    F.trim("codigo_comuna").cast("int").alias("codigo_comuna"),
    F.col("nombre_comuna").alias("nombre_comuna"),
)

dim_stats = dim_df.agg(
    F.count("*").alias("rows"),
    F.countDistinct("codigo_comuna").alias("distinct_keys"),
    F.sum(F.col("codigo_comuna").isNull().cast("int")).alias("null_keys"),
    F.sum(F.col("nombre_comuna").isNull().cast("int")).alias("null_names"),
).first()
print("Master dimension:", dim_stats.asDict())
check(
    "DQ-S06",
    "master dimension: 32 rows, 32 distinct non-null keys, names present",
    dim_stats["rows"] == EXPECTED_MASTER_KEYS
    and dim_stats["distinct_keys"] == EXPECTED_MASTER_KEYS
    and dim_stats["null_keys"] == 0
    and dim_stats["null_names"] == 0,
    dim_stats.asDict(),
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Commune-row classification
# MAGIC
# MAGIC Semantic classification of every Bronze row, not by position. A row is a commune row only if `trim(codigo)` has 4 or 5 digits.
# MAGIC The cast to `INT` happens only after classification, so notes never turn into silent nulls.

# COMMAND ----------

codigo_trim = F.trim(F.col("codigo"))

classified_df = bronze_df.withColumn(
    "codigo_class",
    F.when(F.col("codigo").isNull(), "NULL")
    .when(codigo_trim.rlike("^[0-9]{4}$"), "4_digits")
    .when(codigo_trim.rlike("^[0-9]{5}$"), "5_digits")
    .otherwise("other"),
)

class_counts = {row["codigo_class"]: row["count"] for row in classified_df.groupBy("codigo_class").count().collect()}
print("Row classes:", class_counts)
print("Non-commune rows (text shown for audit):")
classified_df.where(~F.col("codigo_class").isin("4_digits", "5_digits")).select("codigo_class", "codigo").show(truncate=80)

candidates_df = classified_df.where(codigo_trim.rlike(COMMUNE_CODE_REGEX)).select(
    codigo_trim.cast("int").alias("codigo_comuna"),
    F.col("nombre_comuna").alias("nombre_comuna_fuente"),
    F.col(POVERTY_SOURCE_COLUMN).alias("pobreza_proporcion"),
    F.col("_source_year"),
)

candidate_stats = candidates_df.agg(
    F.count("*").alias("rows"),
    F.countDistinct("codigo_comuna").alias("distinct_codes"),
    F.sum(F.col("codigo_comuna").isNull().cast("int")).alias("null_codes"),
).first()
non_commune_rows = bronze_count - candidate_stats["rows"]

print("4-digit commune codes:", class_counts.get("4_digits", 0))
print("5-digit commune codes:", class_counts.get("5_digits", 0))
check("DQ-S07", "valid commune-code rows in Bronze", candidate_stats["rows"] == EXPECTED_VALID_COMMUNE_ROWS, candidate_stats["rows"])
check("DQ-S08", "non-commune rows removed", non_commune_rows == EXPECTED_NON_COMMUNE_ROWS, non_commune_rows)
# Uniqueness is asserted, not enforced: no dropDuplicates.
check("DQ-S09", "distinct valid commune codes (no duplicate codes)", candidate_stats["distinct_codes"] == EXPECTED_VALID_COMMUNE_ROWS, candidate_stats["distinct_codes"])
check("DQ-S10", "valid codes cast to codigo_comuna without nulls", candidate_stats["null_codes"] == 0, candidate_stats["null_codes"])

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Territorial filter by the master dimension
# MAGIC
# MAGIC `INNER JOIN` on `codigo_comuna`. Valid codes outside the master dimension are outside the analytical universe, not errors.

# COMMAND ----------

scoped_df = candidates_df.join(dim_df, on="codigo_comuna", how="inner")

matched_keys = scoped_df.select("codigo_comuna").distinct().count()
outside_master = candidates_df.join(dim_df, on="codigo_comuna", how="left_anti").count()
missing_master = dim_df.join(candidates_df, on="codigo_comuna", how="left_anti")
missing_master_count = missing_master.count()

print("Valid codes outside the master dimension (out of scope):", outside_master)
if missing_master_count:
    missing_master.show(truncate=False)
check("DQ-S11", "intersection with master dimension", matched_keys == EXPECTED_MASTER_KEYS, matched_keys)
check("DQ-S12", "master keys missing from source", missing_master_count == 0, missing_master_count)

scoped_df.explain("formatted")  # educational: small dimension join; not a PASS criterion

# Name diagnostics only: the key already resolved the entity.
name_diff_df = scoped_df.where(F.col("nombre_comuna_fuente") != F.col("nombre_comuna"))
print("Observation - source names that differ textually from canonical names:", name_diff_df.count())
name_diff_df.select("codigo_comuna", "nombre_comuna_fuente", "nombre_comuna").orderBy("codigo_comuna").show(5, truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. Silver derivation
# MAGIC
# MAGIC - `nombre_comuna`: canonical name from the master dimension.
# MAGIC - `pobreza_ingresos_pct`: Bronze proportion (exact decimal) × 100, rounded to 4 decimals with `round` (HALF_UP), `DECIMAL(7,4)`.
# MAGIC   The local pipeline uses pandas `round(4)` on float64; HALF_UP and HALF_EVEN give the same result for all 345 source values (R04 §8), and
# MAGIC   EQ-S06 verifies the result against the baseline.
# MAGIC - `anio_pobreza`: Bronze `_source_year` (validated = 2022 in DQ-S03), as `INT`.

# COMMAND ----------

proportion_stats = scoped_df.agg(
    F.sum(F.col("pobreza_proporcion").isNull().cast("int")).alias("nulls"),
    F.min("pobreza_proporcion").alias("min"),
    F.max("pobreza_proporcion").alias("max"),
).first()
check(
    "DQ-S18",
    "poverty proportion valid before transform (0 nulls, 0–1)",
    proportion_stats["nulls"] == 0 and proportion_stats["min"] >= 0 and proportion_stats["max"] <= 1,
    proportion_stats.asDict(),
)

silver_df = scoped_df.select(
    F.col("codigo_comuna").cast("int").alias("codigo_comuna"),
    F.col("nombre_comuna").cast("string").alias("nombre_comuna"),
    F.round(F.col("pobreza_proporcion") * F.lit(100), 4).cast("decimal(7,4)").alias("pobreza_ingresos_pct"),
    F.col("_source_year").cast("int").alias("anio_pobreza"),
)
silver_df.printSchema()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 9. Silver Data Quality (pre-write)

# COMMAND ----------

silver_stats = silver_df.agg(
    F.count("*").alias("rows"),
    F.countDistinct("codigo_comuna").alias("distinct_keys"),
    F.sum(F.col("codigo_comuna").isNull().cast("int")).alias("null_keys"),
    F.sum(F.col("nombre_comuna").isNull().cast("int")).alias("null_names"),
    F.sum(F.col("pobreza_ingresos_pct").isNull().cast("int")).alias("null_pct"),
    F.min("pobreza_ingresos_pct").alias("min_pct"),
    F.max("pobreza_ingresos_pct").alias("max_pct"),
    F.collect_set("anio_pobreza").alias("years"),
).first()
print("Silver stats:", silver_stats.asDict())

silver_keys_outside_master = silver_df.join(dim_df, on="codigo_comuna", how="left_anti").count()
master_keys_outside_silver = dim_df.join(silver_df, on="codigo_comuna", how="left_anti").count()
silver_schema = [(field.name, field.dataType.simpleString()) for field in silver_df.schema.fields]

check("DQ-S13", "Silver row count", silver_stats["rows"] == EXPECTED_MASTER_KEYS, silver_stats["rows"])
check("DQ-S14", "codigo_comuna non-null", silver_stats["null_keys"] == 0, silver_stats["null_keys"])
check("DQ-S15", "codigo_comuna unique", silver_stats["distinct_keys"] == silver_stats["rows"], f"distinct={silver_stats['distinct_keys']} rows={silver_stats['rows']}")
check(
    "DQ-S16",
    "Silver key coverage = master (0 missing, 0 extra)",
    silver_keys_outside_master == 0 and master_keys_outside_silver == 0,
    f"silver_only={silver_keys_outside_master} master_only={master_keys_outside_silver}",
)
check("DQ-S17", "nombre_comuna non-null", silver_stats["null_names"] == 0, silver_stats["null_names"])
check("DQ-S19", "pobreza_ingresos_pct non-null", silver_stats["null_pct"] == 0, silver_stats["null_pct"])
check(
    "DQ-S20",
    "pobreza_ingresos_pct within 0–100",
    silver_stats["min_pct"] >= 0 and silver_stats["max_pct"] <= 100,
    f"min={silver_stats['min_pct']} max={silver_stats['max_pct']}",
)
check("DQ-S21", "anio_pobreza only 2022", silver_stats["years"] == [SOURCE_YEAR], silver_stats["years"])
check("DQ-S22", "Silver schema = contract", silver_schema == EXPECTED_SILVER_SCHEMA, silver_schema)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 10. Baseline equivalence (pre-write)
# MAGIC
# MAGIC Key-based comparison, never by row order.
# MAGIC - Fixture A `pobreza_staging.csv`: `codigo_comuna`, `nombre_comuna`, `pobreza_ingresos_pct`.
# MAGIC - Fixture B `desigualdad_comunal_final.csv`: only `codigo_comuna` + `anio_pobreza` (C04-A: staging has no year).
# MAGIC
# MAGIC Fixtures are read as text and cast explicitly; they are validation evidence only and are never written to Delta.

# COMMAND ----------

staging_raw_df = spark.read.option("header", True).option("encoding", "UTF-8").csv(STAGING_FIXTURE_PATH)
processed_raw_df = spark.read.option("header", True).option("encoding", "UTF-8").csv(PROCESSED_FIXTURE_PATH)
staging_raw_df.printSchema()
print("Processed fixture columns:", processed_raw_df.columns)

# Wide decimal: casting the fixture value must not round it.
baseline_df = staging_raw_df.select(
    F.col("codigo_comuna").alias("codigo_raw"),
    F.col("pobreza_ingresos_pct").alias("pct_raw"),
    F.trim("codigo_comuna").cast("int").alias("codigo_comuna"),
    F.col("nombre_comuna"),
    F.trim("pobreza_ingresos_pct").cast("decimal(20,10)").alias("pobreza_ingresos_pct"),
)
year_fixture_df = processed_raw_df.select(
    F.col("anio_pobreza").alias("anio_raw"),
    F.trim("codigo_comuna").cast("int").alias("codigo_comuna"),
    F.trim("anio_pobreza").cast("int").alias("anio_pobreza"),
)

baseline_stats = baseline_df.agg(
    F.count("*").alias("rows"),
    F.countDistinct("codigo_comuna").alias("distinct_keys"),
    F.sum(F.col("codigo_comuna").isNull().cast("int")).alias("null_keys"),
    F.sum(F.col("nombre_comuna").isNull().cast("int")).alias("null_names"),
    F.sum(F.col("pobreza_ingresos_pct").isNull().cast("int")).alias("null_pct"),
    F.sum((F.col("codigo_raw").isNotNull() & F.col("codigo_comuna").isNull()).cast("int")).alias("uncastable_keys"),
    F.sum((F.col("pct_raw").isNotNull() & F.col("pobreza_ingresos_pct").isNull()).cast("int")).alias("uncastable_pct"),
).first()
year_stats = year_fixture_df.agg(
    F.count("*").alias("rows"),
    F.countDistinct("codigo_comuna").alias("distinct_keys"),
    F.sum(F.col("anio_pobreza").isNull().cast("int")).alias("null_years"),
    F.sum((F.col("anio_raw").isNotNull() & F.col("anio_pobreza").isNull()).cast("int")).alias("uncastable_years"),
).first()
print("Fixture A stats:", baseline_stats.asDict())
print("Fixture B stats:", year_stats.asDict())

check("EQ-S01", "baseline row count", baseline_stats["rows"] == EXPECTED_MASTER_KEYS, baseline_stats["rows"])
check(
    "EQ-S02",
    "baseline keys: 32 distinct, 0 null, 0 duplicate",
    baseline_stats["distinct_keys"] == EXPECTED_MASTER_KEYS and baseline_stats["null_keys"] == 0,
    f"distinct={baseline_stats['distinct_keys']} null={baseline_stats['null_keys']}",
)

comparison_df = silver_df.alias("s").join(baseline_df.alias("b"), on="codigo_comuna", how="full_outer")
comparison_stats = comparison_df.agg(
    F.sum((F.col("s.nombre_comuna").isNotNull() & F.col("b.nombre_comuna").isNotNull()).cast("int")).alias("matched"),
    F.sum(F.col("b.nombre_comuna").isNull().cast("int")).alias("silver_only"),
    F.sum(F.col("s.nombre_comuna").isNull().cast("int")).alias("baseline_only"),
    F.sum((F.col("s.nombre_comuna") != F.col("b.nombre_comuna")).cast("int")).alias("name_mismatches"),
    F.max(F.abs(F.col("s.pobreza_ingresos_pct") - F.col("b.pobreza_ingresos_pct"))).alias("max_abs_diff"),
    F.sum(
        (F.abs(F.col("s.pobreza_ingresos_pct") - F.col("b.pobreza_ingresos_pct")) > F.lit(Decimal(str(EQUIVALENCE_TOLERANCE)))).cast("int")
    ).alias("mismatch_count"),
).first()
print("Silver vs fixture A:", comparison_stats.asDict())

check(
    "EQ-S03",
    "Silver key set = baseline key set (both directions)",
    comparison_stats["silver_only"] == 0 and comparison_stats["baseline_only"] == 0,
    f"silver_only={comparison_stats['silver_only']} baseline_only={comparison_stats['baseline_only']}",
)
check("EQ-S04", "canonical nombre_comuna equal by key", comparison_stats["name_mismatches"] == 0, comparison_stats["name_mismatches"])

year_comparison = silver_df.select("codigo_comuna", "anio_pobreza").alias("s").join(
    year_fixture_df.select("codigo_comuna", "anio_pobreza").alias("l"), on="codigo_comuna", how="full_outer"
)
year_comparison_stats = year_comparison.agg(
    F.sum((F.col("s.anio_pobreza").isNotNull() & F.col("l.anio_pobreza").isNotNull()).cast("int")).alias("matched"),
    F.sum(F.col("l.anio_pobreza").isNull().cast("int")).alias("silver_only"),
    F.sum(F.col("s.anio_pobreza").isNull().cast("int")).alias("local_only"),
    F.sum((F.col("s.anio_pobreza") != F.col("l.anio_pobreza")).cast("int")).alias("year_mismatches"),
).first()
print("Silver vs fixture B (year):", year_comparison_stats.asDict())
check(
    "EQ-S05",
    "anio_pobreza exact by codigo_comuna vs desigualdad_comunal_final.csv",
    year_comparison_stats["matched"] == EXPECTED_MASTER_KEYS
    and year_comparison_stats["silver_only"] == 0
    and year_comparison_stats["local_only"] == 0
    and year_comparison_stats["year_mismatches"] == 0
    and year_stats["distinct_keys"] == year_stats["rows"] == EXPECTED_MASTER_KEYS,
    year_comparison_stats.asDict(),
)

max_abs_diff = comparison_stats["max_abs_diff"]
print("tolerance     :", EQUIVALENCE_TOLERANCE)
print("max_abs_diff  :", max_abs_diff)
print("mismatch_count:", comparison_stats["mismatch_count"])
check(
    "EQ-S06",
    "pobreza_ingresos_pct abs diff <= tolerance",
    max_abs_diff is not None and float(max_abs_diff) <= EQUIVALENCE_TOLERANCE and comparison_stats["mismatch_count"] == 0,
    f"max_abs_diff={max_abs_diff} mismatch_count={comparison_stats['mismatch_count']} tolerance={EQUIVALENCE_TOLERANCE}",
)
check(
    "EQ-S07",
    "null profile equivalent (0 nulls in compared columns, both sides)",
    silver_stats["null_keys"] == silver_stats["null_names"] == silver_stats["null_pct"] == 0
    and baseline_stats["null_keys"] == baseline_stats["null_names"] == baseline_stats["null_pct"] == 0
    and year_stats["null_years"] == 0,
    f"silver=({silver_stats['null_keys']},{silver_stats['null_names']},{silver_stats['null_pct']}) "
    f"baseline=({baseline_stats['null_keys']},{baseline_stats['null_names']},{baseline_stats['null_pct']}) year_fixture={year_stats['null_years']}",
)
check(
    "EQ-S08",
    "duplicate profile: 0 duplicate keys in Silver and baseline",
    silver_stats["distinct_keys"] == silver_stats["rows"] and baseline_stats["distinct_keys"] == baseline_stats["rows"],
    f"silver={silver_stats['rows'] - silver_stats['distinct_keys']} baseline={baseline_stats['rows'] - baseline_stats['distinct_keys']}",
)
check(
    "EQ-S09",
    "semantic types equivalent (every fixture value casts cleanly to the Silver semantic type)",
    baseline_stats["uncastable_keys"] == 0 and baseline_stats["uncastable_pct"] == 0 and year_stats["uncastable_years"] == 0,
    f"uncastable keys={baseline_stats['uncastable_keys']} pct={baseline_stats['uncastable_pct']} years={year_stats['uncastable_years']}",
)
check(
    "EQ-S10",
    "joined comparison coverage: 32 matched / 0 unmatched",
    comparison_stats["matched"] == EXPECTED_MASTER_KEYS and comparison_stats["silver_only"] == 0 and comparison_stats["baseline_only"] == 0,
    f"matched={comparison_stats['matched']}",
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 11. Delta write (managed table, snapshot overwrite)
# MAGIC
# MAGIC Reached only if every DQ and EQ check above passed. No `LOCATION`, no partitioning, no `mergeSchema`/`overwriteSchema`, no `MERGE`.

# COMMAND ----------

(
    silver_df.write
    .format("delta")
    .mode("overwrite")
    .saveAsTable(TARGET_TABLE)
)
print("Write finished:", TARGET_TABLE)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 12. Post-write Delta validation

# COMMAND ----------

check("DQ-S23", "Silver table exists after write", spark.catalog.tableExists(TARGET_TABLE), TARGET_TABLE)

silver_detail = spark.sql(f"DESCRIBE DETAIL {TARGET_TABLE}").first()
print("format   :", silver_detail["format"])
print("location :", silver_detail["location"])
print("numFiles :", silver_detail["numFiles"])
check("DQ-S24", "DESCRIBE DETAIL format = delta", silver_detail["format"] == "delta", silver_detail["format"])

persisted_df = spark.table(TARGET_TABLE)
persisted_count = persisted_df.count()
check("DQ-S25", "Delta post-write row count", persisted_count == EXPECTED_MASTER_KEYS, persisted_count)

# The validated DataFrame is recomputed from Bronze (lazy evaluation); the dataset is tiny, so no cache.
persisted_vs_validated = persisted_df.exceptAll(silver_df).count() + silver_df.exceptAll(persisted_df).count()
check("DQ-S26", "persisted rows equal the validated Silver rows", persisted_vs_validated == 0, persisted_vs_validated)

spark.sql(f"DESCRIBE TABLE {TARGET_TABLE}").show(truncate=False)
(
    spark.sql(f"DESCRIBE HISTORY {TARGET_TABLE}")
    .select(
        "version",
        "timestamp",
        "operation",
        F.col("operationParameters")["mode"].alias("mode"),
        F.col("operationMetrics")["numOutputRows"].alias("numOutputRows"),
    )
    .orderBy("version")
    .show(truncate=False)
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 13. Evidence summary

# COMMAND ----------

print("Bronze rows                       ", bronze_count)
print("valid commune rows                ", candidate_stats["rows"], f"(4 digits={class_counts.get('4_digits', 0)}, 5 digits={class_counts.get('5_digits', 0)})")
print("non-commune rows                  ", non_commune_rows, f"(NULL={class_counts.get('NULL', 0)}, other={class_counts.get('other', 0)})")
print("valid commune codes outside master", outside_master)
print("master commune rows               ", dim_stats["rows"])
print("master keys missing from source   ", missing_master_count)
print("Silver candidate rows             ", silver_stats["rows"])
print("Silver Delta rows                 ", persisted_count)
print("equivalence tolerance / max diff  ", EQUIVALENCE_TOLERANCE, "/", max_abs_diff)
print("target existed before this run    ", target_existed_before)
print()
for check_id, description, status, _ in dq_results:
    print(f"  {status}  {check_id}  {description}")
