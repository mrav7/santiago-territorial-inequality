# Databricks notebook source
# MAGIC %md
# MAGIC # 04 · Bronze SINIM — SpreadsheetML/XML 2003 (A/B)
# MAGIC
# MAGIC Run all on serverless, then Run all again for snapshot rerun evidence.
# MAGIC Upload this notebook under `databricks/notebooks/` and the ordinary Python
# MAGIC files `spreadsheetml.py` / `__init__.py` under sibling `databricks/src/ingestion/`.
# MAGIC Preserve these relative paths in Workspace; Git integration is not required.
# MAGIC The module must be a Workspace **file**, not a notebook. Restart Python after
# MAGIC replacing code before reviewing runtime evidence. No libraries are installed.
# MAGIC
# MAGIC Values remain strings. All source body rows are retained, including null rows.
# MAGIC Both candidates and existing targets pass preflight before either write.
# MAGIC Writes are sequential per table, not an atomic transaction across A and B.

# COMMAND ----------

import hashlib
import importlib
import os
from pathlib import Path
import sys
from datetime import datetime, timezone

from pyspark.sql import functions as F
from pyspark.sql.types import StringType, StructField, StructType

# Default CWD in current Databricks runtimes is the notebook's directory.
# Fail explicitly if the human upload did not preserve the sibling src directory.
MODULE_ROOT = (Path.cwd().parent / "src").resolve()
MODULE_FILE = MODULE_ROOT / "ingestion/spreadsheetml.py"
if not MODULE_FILE.is_file():
    raise RuntimeError(
        f"BLOCKED: missing {MODULE_FILE}. Upload databricks/src/ingestion as Python "
        "Workspace files alongside databricks/notebooks; do not paste/duplicate the parser."
    )
sys.path.insert(0, str(MODULE_ROOT))
from ingestion import spreadsheetml
if Path(spreadsheetml.__file__).resolve() != MODULE_FILE:
    raise RuntimeError("BLOCKED: ingestion.spreadsheetml resolved to an unexpected module")
spreadsheetml = importlib.reload(spreadsheetml)
print("Parser module:", spreadsheetml.__file__)
print("Parser SHA-256:", hashlib.sha256(MODULE_FILE.read_bytes()).hexdigest())

# Measured from versioned raw files at HEAD 6f6a0ecfa96e836edb094cfc5a45d0476977bbf1.
SOURCES = [
    {
        "id": "A", "dataset": "sinim_areas_verdes",
        "file": "datos_municipales_20260402222841_Sin-Corrección-Monetaria.xls",
        "bytes": 16619,
        "sha256": "f3b4e6615f1e4c37670ccafe4bc21f7b293f64a10a11e6d2386743088f86c058",
        "columns": ["codigo_comuna", "nombre_comuna", "mmpqc_2024", "mmpzc_2024"],
    },
    {
        "id": "B", "dataset": "sinim_capacidad_municipal",
        "file": "datos_municipales_20260402223904_Sin-Corrección-Monetaria.xls",
        "bytes": 13697,
        "sha256": "6501a194b97305bd8624802a9d01c61eb0cf1cfd8a6ef85f4b1b1ff50e79d843",
        "columns": ["codigo_comuna", "nombre_comuna", "iadm41_2024"],
    },
]
VOLUME = "/Volumes/workspace/bronze/source_files"
METADATA = ["_source_dataset", "_source_file", "_source_path", "_source_year", "_ingested_at_utc"]
results = []


def check(source, number, description, passed, detail=""):
    check_id = f"DQ-B{source['id']}{number:02d}"
    status = "PASS" if passed else "FAIL"
    results.append((check_id, description, status, str(detail)))
    print(f"[{status}] {check_id}: {description} :: {detail}")
    if not passed:
        raise RuntimeError(f"BLOCKED: {check_id}: {description} :: {detail}")


def signature(df):
    return [(field.name, field.dataType.simpleString()) for field in df.schema.fields]


def difference(left, right):
    # exceptAll preserves duplicate multiplicities and uses null-safe set semantics.
    return left.exceptAll(right).count(), right.exceptAll(left).count()


def latest_version(table):
    return spark.sql(f"DESCRIBE HISTORY {table}").agg(F.max("version")).first()[0]


def managed_types(source):
    return [r["table_type"] for r in spark.sql(
        "SELECT table_type FROM workspace.information_schema.tables "
        f"WHERE table_schema = 'bronze' AND table_name = '{source['dataset']}'"
    ).collect()]


def metadata_valid(df, source):
    expected = {"_source_dataset": source["dataset"], "_source_file": source["file"],
                "_source_path": source["path"], "_source_year": 2024}
    invalid = F.lit(False)
    for column, value in expected.items():
        invalid = invalid | ~F.col(column).eqNullSafe(F.lit(value))
    invalid = invalid | F.col("_ingested_at_utc").isNull()
    bad = df.where(invalid).count()
    timestamps = df.select("_ingested_at_utc").distinct().count()
    print("Metadata profile:")
    df.groupBy(*METADATA).count().show(truncate=False)
    return bad == 0 and timestamps == 1, f"invalid_rows={bad}; timestamps={timestamps}"


print("Python:", sys.version)
print("Spark:", spark.version)
print("CWD:", os.getcwd())
spark.conf.set("spark.sql.session.timeZone", "UTC")
print("Session timezone:", spark.conf.get("spark.sql.session.timeZone"))
assert spark.range(1).count() == 1, "Spark runtime action failed"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Identity, parsing, Spark construction and Bronze quality
# MAGIC
# MAGIC The parser returns XML text + nulls, technical headers and structure evidence.
# MAGIC Spark creates explicit STRING fields, performs checks/profiles and writes Delta.
# MAGIC No business typing, token mapping, territorial filtering or derived metrics.

# COMMAND ----------

prepared = []
for source in SOURCES:
    source = dict(source)
    source["path"] = f"{VOLUME}/{source['file']}"
    source["table"] = f"workspace.bronze.{source['dataset']}"
    path = Path(source["path"])
    print("\nSOURCE", source["id"], source["path"])
    check(source, 1, "Volume file exists", path.is_file(), source["path"])
    content = path.read_bytes()
    check(source, 2, "source size equals versioned raw", len(content) == source["bytes"], len(content))
    digest = hashlib.sha256(content).hexdigest()
    check(source, 3, "source SHA-256 equals versioned raw", digest == source["sha256"], digest)
    try:
        parsed = spreadsheetml.parse_spreadsheetml(content, "Hoja1", skiprows=2)
    except Exception as error:
        check(source, 4, "XML Workbook, explicit Hoja1, Table and header parse", False, str(error))
    check(source, 4, "XML Workbook, explicit Hoja1, Table and header parse", True, parsed.sheet)
    print("Parser strategy: ElementTree SpreadsheetML/XML 2003")
    print("XML rows / body rows / width:", parsed.xml_row_count, len(parsed.rows), parsed.width)
    print("Original descriptors:", parsed.descriptors)
    print("Original header:", parsed.header)
    print("Technical columns:", parsed.columns)
    print("Observed ss:Type (diagnostic only):", parsed.observed_data_types)
    print("First three rows:", parsed.rows[:3])
    check(source, 5, "exact current technical columns in order", parsed.columns == source["columns"], parsed.columns)
    check(source, 6, "names nonempty, unique and body widths aligned",
          all(parsed.columns) and len(set(parsed.columns)) == len(parsed.columns)
          and all(len(row) == parsed.width for row in parsed.rows), parsed.width)
    check(source, 7, "nonempty body with the observed 52 source rows", len(parsed.rows) == 52, len(parsed.rows))
    schema = StructType([StructField(c, StringType(), True) for c in parsed.columns])
    raw_df = spark.createDataFrame(parsed.rows, schema=schema)
    # A driver literal makes the timestamp stable even across separate Spark actions.
    ingested_at = datetime.now(timezone.utc)
    candidate = raw_df.select(
        "*", F.lit(source["dataset"]).alias("_source_dataset"),
        F.lit(source["file"]).alias("_source_file"), F.lit(source["path"]).alias("_source_path"),
        F.lit(2024).cast("int").alias("_source_year"),
        F.lit(ingested_at).cast("timestamp").alias("_ingested_at_utc"),
    )
    candidate.printSchema()
    expected_schema = [(c, "string") for c in parsed.columns] + [
        ("_source_dataset", "string"), ("_source_file", "string"), ("_source_path", "string"),
        ("_source_year", "int"), ("_ingested_at_utc", "timestamp"),
    ]
    count = candidate.count()
    check(source, 8, "explicit STRING source schema and five metadata types", signature(candidate) == expected_schema, signature(candidate))
    check(source, 9, "Spark preserves all parsed rows", count == len(parsed.rows), count)
    valid, profile = metadata_valid(candidate, source)
    check(source, 10, "all expected metadata values and one nonnull snapshot timestamp", valid, profile)
    # Profiles never remove or alter rows.
    candidate.agg(*[F.sum(F.col(c).isNull().cast("int")).alias(c) for c in parsed.columns]).show()
    print("Codes present:", candidate.where(F.col("codigo_comuna").isNotNull()).count())
    print("Distinct codes:", candidate.select("codigo_comuna").distinct().count())
    print("Duplicate source rows:", count - raw_df.distinct().count())
    for token in ("No Aplica", "No Recepcionado"):
        candidate.agg(*[F.sum(F.when(F.col(c) == token, 1).otherwise(0)).alias(c) for c in parsed.columns]).show()
        print("Token above:", repr(token))
    logical_columns = parsed.columns + METADATA[:-1]
    prepared.append({"source": source, "candidate": candidate, "logical": logical_columns,
                     "schema": expected_schema, "count": count})

# COMMAND ----------

# MAGIC %md
# MAGIC ## Existing-target compatibility — both tables before any write
# MAGIC
# MAGIC Managed Delta + exact schema + expected source metadata + identical row multiset.
# MAGIC An ambiguous/incompatible target blocks the run. No overwrite permission flag.
# MAGIC The verified source is pinned; changed input requires a separately reviewed contract.

# COMMAND ----------

for item in prepared:
    source, candidate = item["source"], item["candidate"]
    table = source["table"]
    existed = spark.catalog.tableExists(table)
    item["existed"], item["version_before"] = existed, None
    print("Target:", table, "existed:", existed)
    if existed:
        try:
            detail = spark.sql(f"DESCRIBE DETAIL {table}").first()
            types = managed_types(source)
        except Exception as error:
            check(source, 11, "existing target is inspectable managed Delta", False, str(error))
        check(source, 11, "existing target is inspectable managed Delta", detail["format"] == "delta" and types == ["MANAGED"], types)
        check(source, 26, "existing target has no artificial partitioning", detail["partitionColumns"] == [], detail["partitionColumns"])
        existing = spark.table(table)
        check(source, 12, "existing target schema compatible", signature(existing) == item["schema"], signature(existing))
        valid, profile = metadata_valid(existing, source)
        check(source, 13, "existing target attributed to expected source snapshot", valid, profile)
        # Materialize differences now; do not retain a lazy target read across overwrite.
        diff = difference(existing.select(item["logical"]), candidate.select(item["logical"]))
        check(source, 14, "existing logical row multiset equals candidate excluding ingestion time", diff == (0, 0), diff)
        item["version_before"] = latest_version(table)
        check(source, 15, "existing Delta version available", item["version_before"] is not None, item["version_before"])
    else:
        print("Initial creation: existing-target checks 11–15 not applicable")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Managed Delta snapshot overwrite, post-write and history
# MAGIC
# MAGIC No LOCATION, append, schema evolution or partitioning. Avoid concurrent writers
# MAGIC during manual validation: existence/version checks are not a cross-table lock.

# COMMAND ----------

for item in prepared:
    source, candidate = item["source"], item["candidate"]
    table = source["table"]
    check(source, 16, "target existence stable since preflight", spark.catalog.tableExists(table) == item["existed"], item["existed"])
    if item["existed"]:
        current_version = latest_version(table)
        check(source, 17, "target version stable before overwrite", current_version == item["version_before"], current_version)
    candidate.write.format("delta").mode("overwrite").saveAsTable(table)
    check(source, 18, "persisted target exists", spark.catalog.tableExists(table), table)
    detail = spark.sql(f"DESCRIBE DETAIL {table}").first()
    types = managed_types(source)
    check(source, 19, "persisted format Delta and UC type MANAGED", detail["format"] == "delta" and types == ["MANAGED"], types)
    check(source, 27, "persisted target has no artificial partitioning", detail["partitionColumns"] == [], detail["partitionColumns"])
    persisted = spark.table(table)
    check(source, 20, "persisted schema equals candidate", signature(persisted) == item["schema"], signature(persisted))
    post_count = persisted.count()
    check(source, 21, "persisted count equals candidate (no accumulation)", post_count == item["count"], post_count)
    valid, profile = metadata_valid(persisted, source)
    check(source, 22, "persisted metadata valid and one snapshot timestamp", valid, profile)
    diff = difference(persisted.select(candidate.columns), candidate)
    check(source, 23, "persisted full row multiset equals candidate including timestamp", diff == (0, 0), diff)
    version_after = latest_version(table)
    check(source, 24, "persisted Delta version available", version_after is not None, version_after)
    if item["existed"]:
        check(source, 25, "rerun creates a newer Delta version", version_after > item["version_before"], version_after)
    print("Source / candidate / persisted rows:", item["count"], item["count"], post_count)
    print("Version before / after:", item["version_before"], version_after)
    spark.sql(f"DESCRIBE DETAIL {table}").show(truncate=False)
    spark.sql(f"DESCRIBE HISTORY {table}").show(truncate=False)

# COMMAND ----------

for check_id, description, status, detail in results:
    print(f"{status} {check_id}: {description} :: {detail}")
print("Initial run does not prove rerun. Preserve both run outputs and independent SQL results.")
