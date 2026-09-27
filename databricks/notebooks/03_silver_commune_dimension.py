# Databricks notebook source
# MAGIC %md
# MAGIC # Silver commune dimension
# MAGIC
# MAGIC Read the versioned master CSV from the managed Volume, validate its identity and
# MAGIC domain contract, then publish `workspace.silver.dim_comuna` as a managed Delta table.
# MAGIC The same notebook supports an initial write and a compatible snapshot rerun.
# MAGIC Every failed check stops execution; run all cells on serverless compute.

# COMMAND ----------

import csv
import hashlib
import os

from pyspark.sql import functions as F
from pyspark.sql.types import StringType, StructField, StructType

SOURCE_PATH = "/Volumes/workspace/bronze/source_files/dim_comuna_base.csv"
TARGET_TABLE = "workspace.silver.dim_comuna"
TABLE_TYPE_QUERY = """
SELECT table_type
FROM workspace.information_schema.tables
WHERE table_schema = 'silver'
  AND table_name = 'dim_comuna'
"""
EXPECTED_SIZE_BYTES = 1779
EXPECTED_SHA256 = "c8e831949b07bbefed64ffd0e50ee73937c657bbb5071b3741007b9e73532aad"
EXPECTED_ROWS = 32
EXPECTED_COLUMNS = [
    "codigo_comuna",
    "nombre_comuna",
    "provincia",
    "region",
    "fuente_referencia",
]
EXPECTED_SCHEMA = [
    ("codigo_comuna", "int"),
    ("nombre_comuna", "string"),
    ("provincia", "string"),
    ("region", "string"),
    ("fuente_referencia", "string"),
]
SOURCE_SCHEMA = StructType([StructField(name, StringType(), True) for name in EXPECTED_COLUMNS])

results = []


def check(name, description, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    results.append((name, description, status, str(detail)))
    print(f"[{status}] {name}: {description} :: {detail}")
    if not passed:
        raise AssertionError(f"{name}: {description} :: {detail}")


def schema_signature(dataframe):
    return [(field.name, field.dataType.simpleString()) for field in dataframe.schema.fields]


def row_difference(left, right):
    return left.exceptAll(right).count(), right.exceptAll(left).count()


def latest_version(table_name):
    return spark.sql(f"DESCRIBE HISTORY {table_name}").agg(F.max("version")).first()[0]


# COMMAND ----------

# MAGIC %md
# MAGIC ## Source identity and explicit read

# COMMAND ----------

check("source_accessible", "master CSV exists in the managed Volume", os.path.isfile(SOURCE_PATH), SOURCE_PATH)
source_size = os.path.getsize(SOURCE_PATH)
check("source_size", "master CSV byte size matches the versioned file", source_size == EXPECTED_SIZE_BYTES, source_size)
with open(SOURCE_PATH, "rb") as source_handle:
    source_sha256 = hashlib.sha256(source_handle.read()).hexdigest()
check("source_sha256", "master CSV SHA-256 matches the versioned file", source_sha256 == EXPECTED_SHA256, source_sha256)

with open(SOURCE_PATH, newline="", encoding="utf-8-sig") as source_handle:
    source_header = next(csv.reader(source_handle), [])
check("source_columns", "CSV header has exactly the expected columns in order", source_header == EXPECTED_COLUMNS, source_header)

source_df = (
    spark.read.schema(SOURCE_SCHEMA)
    .option("header", True)
    .option("enforceSchema", False)
    .option("mode", "FAILFAST")
    .option("encoding", "UTF-8")
    .csv(SOURCE_PATH)
)
check("source_read_schema", "source read uses the five explicit string columns", schema_signature(source_df) == [(name, "string") for name in EXPECTED_COLUMNS], schema_signature(source_df))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Source quality before typing

# COMMAND ----------

key_text = F.trim(F.col("codigo_comuna"))
typed_key = F.expr("try_cast(trim(codigo_comuna) AS INT)")
source_stats = source_df.agg(
    F.count("*").alias("rows"),
    F.sum((F.col("codigo_comuna").isNull() | (key_text == "")).cast("int")).alias("blank_keys"),
    F.sum((key_text.isNotNull() & (key_text != "") & typed_key.isNull()).cast("int")).alias("uncastable_keys"),
    F.countDistinct(typed_key).alias("distinct_keys"),
    F.sum((F.col("nombre_comuna").isNull() | (F.trim("nombre_comuna") == "")).cast("int")).alias("blank_names"),
    F.countDistinct("nombre_comuna").alias("distinct_names"),
    F.sum((F.col("fuente_referencia").isNull() | (F.trim("fuente_referencia") == "")).cast("int")).alias("blank_references"),
).first()
print("Source profile:", source_stats.asDict())
check("source_rows", "master CSV contains exactly 32 rows", source_stats["rows"] == EXPECTED_ROWS, source_stats["rows"])
check("source_key_presence", "source commune codes are neither null nor blank", source_stats["blank_keys"] == 0, source_stats["blank_keys"])
check("source_key_cast", "all source commune codes convert to INT", source_stats["uncastable_keys"] == 0, source_stats["uncastable_keys"])
check("source_key_distinct", "source contains 32 distinct commune codes", source_stats["distinct_keys"] == EXPECTED_ROWS, source_stats["distinct_keys"])
source_duplicate_keys = source_df.withColumn("typed_key", typed_key).groupBy("typed_key").count().where("count > 1").count()
check("source_key_duplicates", "source has no duplicate commune codes after casting", source_duplicate_keys == 0, source_duplicate_keys)
check("source_name_presence", "source commune names are neither null nor blank", source_stats["blank_names"] == 0, source_stats["blank_names"])
check("source_name_distinct", "source contains 32 distinct commune names", source_stats["distinct_names"] == EXPECTED_ROWS, source_stats["distinct_names"])
source_provinces = [row[0] for row in source_df.select("provincia").distinct().collect()]
source_regions = [row[0] for row in source_df.select("region").distinct().collect()]
check("source_province", "source province is exactly SANTIAGO", source_provinces == ["SANTIAGO"], source_provinces)
check("source_region", "source region is exactly METROPOLITANA DE SANTIAGO", source_regions == ["METROPOLITANA DE SANTIAGO"], source_regions)
check("source_reference_presence", "source references are neither null nor blank", source_stats["blank_references"] == 0, source_stats["blank_references"])

# COMMAND ----------

# MAGIC %md
# MAGIC ## Candidate and source equivalence

# COMMAND ----------

source_typed_df = source_df.select(typed_key.alias("codigo_comuna"), *[F.col(name) for name in EXPECTED_COLUMNS[1:]])
candidate_df = source_df.select(
    typed_key.alias("codigo_comuna"),
    *[F.trim(F.col(name)).alias(name) for name in EXPECTED_COLUMNS[1:]],
)
candidate_stats = candidate_df.agg(
    F.count("*").alias("rows"),
    F.countDistinct("codigo_comuna").alias("distinct_keys"),
    F.sum(F.col("codigo_comuna").isNull().cast("int")).alias("null_keys"),
).first()
check("candidate_rows", "Silver candidate has exactly 32 rows", candidate_stats["rows"] == EXPECTED_ROWS, candidate_stats.asDict())
check("candidate_schema", "Silver candidate has the exact ordered five-column contract", schema_signature(candidate_df) == EXPECTED_SCHEMA, schema_signature(candidate_df))
check("candidate_keys", "Silver candidate has 32 distinct non-null INT keys", candidate_stats["distinct_keys"] == EXPECTED_ROWS and candidate_stats["null_keys"] == 0, candidate_stats.asDict())

source_only_keys = source_typed_df.select("codigo_comuna").join(candidate_df.select("codigo_comuna"), "codigo_comuna", "left_anti").count()
candidate_only_keys = candidate_df.select("codigo_comuna").join(source_typed_df.select("codigo_comuna"), "codigo_comuna", "left_anti").count()
matched_keys = source_typed_df.select("codigo_comuna").join(candidate_df.select("codigo_comuna"), "codigo_comuna").count()
check("key_equivalence", "source and candidate match on all 32 codes with no missing or extra keys", matched_keys == EXPECTED_ROWS and source_only_keys == 0 and candidate_only_keys == 0, f"matched={matched_keys} source_only={source_only_keys} candidate_only={candidate_only_keys}")

joined = source_typed_df.alias("source").join(candidate_df.alias("candidate"), "codigo_comuna")
for name in EXPECTED_COLUMNS[1:]:
    mismatches = joined.where(~F.col(f"source.{name}").eqNullSafe(F.col(f"candidate.{name}"))).count()
    check(f"exact_{name}", f"{name} is unchanged from the master CSV for every commune code", mismatches == 0, mismatches)

candidate_provinces = [row[0] for row in candidate_df.select("provincia").distinct().collect()]
candidate_regions = [row[0] for row in candidate_df.select("region").distinct().collect()]
check("candidate_territory", "Silver candidate retains the required province and region", candidate_provinces == ["SANTIAGO"] and candidate_regions == ["METROPOLITANA DE SANTIAGO"], f"province={candidate_provinces} region={candidate_regions}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Existing target compatibility before overwrite

# COMMAND ----------

target_existed_before = spark.catalog.tableExists(TARGET_TABLE)
print("Target existed before run:", target_existed_before)
version_before = None
if target_existed_before:
    try:
        target_format = spark.sql(f"DESCRIBE DETAIL {TARGET_TABLE}").first()["format"]
    except Exception as error:
        raise RuntimeError(f"Existing commune dimension cannot be inspected as a Delta table: {error}") from error
    check("target_format", "existing commune dimension is Delta", target_format == "delta", target_format)
    target_table_types = [row["table_type"] for row in spark.sql(TABLE_TYPE_QUERY).collect()]
    check("target_managed", "existing commune dimension has exactly one MANAGED Unity Catalog entry", target_table_types == ["MANAGED"], target_table_types)
    existing_df = spark.table(TARGET_TABLE)
    check("target_schema", "existing commune dimension has the exact ordered schema", schema_signature(existing_df) == EXPECTED_SCHEMA, schema_signature(existing_df))
    target_stats = existing_df.agg(
        F.count("*").alias("rows"),
        F.countDistinct("codigo_comuna").alias("distinct_keys"),
        F.sum(F.col("codigo_comuna").isNull().cast("int")).alias("null_keys"),
    ).first()
    check("target_keys", "existing commune dimension has 32 distinct non-null keys", target_stats["rows"] == EXPECTED_ROWS and target_stats["distinct_keys"] == EXPECTED_ROWS and target_stats["null_keys"] == 0, target_stats.asDict())
    target_only_keys = existing_df.select("codigo_comuna").join(source_typed_df.select("codigo_comuna"), "codigo_comuna", "left_anti").count()
    source_only_target_keys = source_typed_df.select("codigo_comuna").join(existing_df.select("codigo_comuna"), "codigo_comuna", "left_anti").count()
    check("target_key_coverage", "existing commune dimension has exactly the master key set", target_only_keys == 0 and source_only_target_keys == 0, f"target_only={target_only_keys} source_only={source_only_target_keys}")
    target_only_rows, candidate_only_rows = row_difference(existing_df, candidate_df)
    check("target_content", "existing commune dimension equals the validated candidate as a row multiset", target_only_rows == 0 and candidate_only_rows == 0, f"target_only={target_only_rows} candidate_only={candidate_only_rows}")
    version_before = latest_version(TARGET_TABLE)
    check("target_history", "existing Delta target has a latest version", version_before is not None, version_before)

check("target_state_stable", "target existence did not change during validation", spark.catalog.tableExists(TARGET_TABLE) == target_existed_before, target_existed_before)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Managed Delta snapshot write and post-write checks

# COMMAND ----------

(
    candidate_df.write
    .format("delta")
    .mode("overwrite")
    .saveAsTable(TARGET_TABLE)
)

check("persisted_exists", "commune dimension exists after the write", spark.catalog.tableExists(TARGET_TABLE), TARGET_TABLE)
persisted_format = spark.sql(f"DESCRIBE DETAIL {TARGET_TABLE}").first()["format"]
check("persisted_format", "persisted commune dimension is Delta", persisted_format == "delta", persisted_format)
persisted_table_types = [row["table_type"] for row in spark.sql(TABLE_TYPE_QUERY).collect()]
check("persisted_managed", "persisted commune dimension has exactly one MANAGED Unity Catalog entry", persisted_table_types == ["MANAGED"], persisted_table_types)
persisted_df = spark.table(TARGET_TABLE)
check("persisted_schema", "persisted commune dimension has the exact ordered schema", schema_signature(persisted_df) == EXPECTED_SCHEMA, schema_signature(persisted_df))
persisted_stats = persisted_df.agg(
    F.count("*").alias("rows"),
    F.countDistinct("codigo_comuna").alias("distinct_keys"),
    F.sum(F.col("codigo_comuna").isNull().cast("int")).alias("null_keys"),
).first()
check("persisted_keys", "persisted commune dimension has 32 rows and 32 distinct non-null keys", persisted_stats["rows"] == EXPECTED_ROWS and persisted_stats["distinct_keys"] == EXPECTED_ROWS and persisted_stats["null_keys"] == 0, persisted_stats.asDict())
persisted_only, candidate_only = row_difference(persisted_df, candidate_df)
check("persisted_content", "persisted rows equal the validated candidate as a row multiset", persisted_only == 0 and candidate_only == 0, f"persisted_only={persisted_only} candidate_only={candidate_only}")
version_after = latest_version(TARGET_TABLE)
check("persisted_history", "Delta history contains a latest version after the write", version_after is not None, version_after)
if target_existed_before:
    check("rerun_version", "snapshot rerun created a newer Delta version", version_after > version_before, f"before={version_before} after={version_after}")

print(f"Source rows / candidate rows / persisted rows: {source_stats['rows']} / {candidate_stats['rows']} / {persisted_stats['rows']}")
print(f"Matched / source-only / candidate-only keys: {matched_keys} / {source_only_keys} / {candidate_only_keys}")
print(f"Target existed before run: {target_existed_before}; Delta version before / after: {version_before} / {version_after}")
for name, description, status, _ in results:
    print(f"{status} {name}: {description}")
