# Databricks notebook source
# MAGIC %md
# MAGIC # 01 · Bronze — Poverty by income (Source C)
# MAGIC
# MAGIC `data/raw/estimaciones_tasa_pobreza_ingresos_comunas_2022.xlsx` → UC Volume → Spark DataFrame → `workspace.bronze.pobreza_ingresos` (Delta).
# MAGIC
# MAGIC Bronze scope only: technical read, technical column naming if Delta requires it, ingestion metadata, Bronze checks, snapshot overwrite.
# MAGIC No filtering, no commune homologation, no proportion → percentage conversion, no Silver column selection.
# MAGIC
# MAGIC Run on serverless notebook compute. Every section prints its evidence; a failed check raises and stops the run.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Configuration

# COMMAND ----------

import hashlib
import os
import sys

from pyspark.sql import functions as F

SOURCE_DATASET = "pobreza_ingresos"
SOURCE_FILE = "estimaciones_tasa_pobreza_ingresos_comunas_2022.xlsx"
SOURCE_PATH = f"/Volumes/workspace/bronze/source_files/{SOURCE_FILE}"
SOURCE_YEAR = 2022
TARGET_TABLE = "workspace.bronze.pobreza_ingresos"

# Identity of the versioned repository file (data/raw/), measured locally before upload.
EXPECTED_SIZE_BYTES = 53824
EXPECTED_SHA256 = "d84f44accb14e73bdd785ccdd61290d298504a3d1afe3d2fea1431804409bcc9"

# Local read contract (data/raw/metadata_fuentes.csv): sheet Estimaciones, skiprows=2.
# In the workbook this means: header on row 3, columns A:J, data up to the last used row (354).
SHEET_NAME = "Estimaciones"
SKIPROWS = 2
DATA_ADDRESS = "Estimaciones!A3:J354"

# Header row observed in the local workbook, after technical normalization (see section 8).
EXPECTED_TECHNICAL_COLUMNS = [
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
]

METADATA_COLUMNS = [
    "_source_dataset",
    "_source_file",
    "_source_path",
    "_source_year",
    "_ingested_at_utc",
]

dq_results = []


def check(check_id, description, passed, detail=""):
    """Record a Bronze check and stop the run if it fails."""
    status = "PASS" if passed else "FAIL"
    dq_results.append((check_id, description, status, str(detail)))
    print(f"[{status}] {check_id} {description} :: {detail}")
    if not passed:
        raise AssertionError(f"{check_id} failed: {description} :: {detail}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Runtime inspection

# COMMAND ----------

print("Python:", sys.version)
print("Spark:", spark.version)
print("Session time zone:", spark.conf.get("spark.sql.session.timeZone"))

# A real Spark action, not just the existence of the `spark` object.
spark_action_count = spark.range(1).count()
print("spark.range(1).count() =", spark_action_count)
assert spark_action_count == 1, "Spark action returned an unexpected result"

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Source-file verification
# MAGIC
# MAGIC The file in the Volume must be byte-identical to the versioned repository file.

# COMMAND ----------

file_exists = os.path.isfile(SOURCE_PATH)
check("DQ-B01", "source file exists in the Volume", file_exists, SOURCE_PATH)

remote_size = os.path.getsize(SOURCE_PATH)
with open(SOURCE_PATH, "rb") as handle:
    remote_sha256 = hashlib.sha256(handle.read()).hexdigest()

print("name  :", os.path.basename(SOURCE_PATH))
print("size  :", remote_size, "bytes (expected", EXPECTED_SIZE_BYTES, ")")
print("sha256:", remote_sha256)
print("expect:", EXPECTED_SHA256)

check(
    "DQ-B02",
    "source file size and SHA-256 match the versioned local file",
    remote_size == EXPECTED_SIZE_BYTES and remote_sha256 == EXPECTED_SHA256,
    f"size={remote_size} sha256={remote_sha256}",
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Excel capability discovery
# MAGIC
# MAGIC Option A: native Spark Excel reader (`format("excel")`), tested with a read-only `listSheets`.
# MAGIC Option B, only if A is unavailable: Python edge decoding with libraries **already present** (pandas + openpyxl). Nothing is installed.

# COMMAND ----------

import importlib.util

excel_reader = None
native_error = None

try:
    sheets_df = (
        spark.read.format("excel")
        .option("operation", "listSheets")
        .load(SOURCE_PATH)
    )
    sheets_rows = sheets_df.collect()
    excel_reader = "native_spark"
except Exception as error:  # the reader may not exist in this runtime
    native_error = f"{type(error).__name__}: {str(error)[:800]}"

if excel_reader == "native_spark":
    sheets_df.printSchema()
    print(sheets_rows)
    sheet_names = [row["sheetName"] for row in sheets_rows]
else:
    print("Native Spark Excel reader NOT available:", native_error)
    has_pandas = importlib.util.find_spec("pandas") is not None
    has_openpyxl = importlib.util.find_spec("openpyxl") is not None
    print("pandas preinstalled:", has_pandas, "| openpyxl preinstalled:", has_openpyxl)
    if not (has_pandas and has_openpyxl):
        raise RuntimeError(
            "BLOCKED: no native Spark Excel reader and no preinstalled pandas/openpyxl. "
            "Do not install packages in P03."
        )
    import openpyxl
    import pandas as pd

    print("pandas", pd.__version__, "| openpyxl", openpyxl.__version__)
    excel_reader = "python_edge"
    sheet_names = pd.ExcelFile(SOURCE_PATH, engine="openpyxl").sheet_names

print("Excel reader strategy:", excel_reader)
print("Sheets:", sheet_names)
check("DQ-B03", f"workbook readable and sheet '{SHEET_NAME}' present", SHEET_NAME in sheet_names, sheet_names)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Source read
# MAGIC
# MAGIC Contract `sheet=Estimaciones, skiprows=2` → header row 3.
# MAGIC - Native: `headerRows=1` + `dataAddress=Estimaciones!A3:J354` (header row, header columns and last used row observed in the workbook).
# MAGIC - Python edge: `pandas.read_excel(sheet_name="Estimaciones", skiprows=2)`, every cell kept as text (Bronze does not type).

# COMMAND ----------

if excel_reader == "native_spark":
    source_df = (
        spark.read.format("excel")
        .option("headerRows", 1)
        .option("dataAddress", DATA_ADDRESS)
        .load(SOURCE_PATH)
    )
    source_parsed_count = source_df.count()
else:
    source_pdf = pd.read_excel(
        SOURCE_PATH,
        sheet_name=SHEET_NAME,
        skiprows=SKIPROWS,
        dtype=object,
        engine="openpyxl",
    )
    source_parsed_count = len(source_pdf)

print("Source parsed row count:", source_parsed_count)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Schema / count inspection (source as read)

# COMMAND ----------

if excel_reader == "native_spark":
    source_df.printSchema()
    source_columns = source_df.columns
else:
    print(source_pdf.dtypes)
    source_columns = [str(name) for name in source_pdf.columns]

print("Source columns (repr):")
for position, name in enumerate(source_columns):
    print(f"  {position}: {name!r}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Spark conversion (Python edge only)
# MAGIC
# MAGIC The pandas frame is converted immediately to Spark with an explicit all-string schema. From here on everything is Spark + Delta.

# COMMAND ----------

from pyspark.sql.types import StringType, StructField, StructType

if excel_reader == "python_edge":
    edge_schema = StructType([StructField(name, StringType(), True) for name in source_columns])
    edge_rows = [
        [None if pd.isna(value) else str(value) for value in row]
        for row in source_pdf.itertuples(index=False, name=None)
    ]
    source_df = spark.createDataFrame(edge_rows, schema=edge_schema)
    print("Converted to Spark:", source_df.count(), "rows")
else:
    print("Not needed: the source was read natively by Spark.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. Technical column names + ingestion metadata
# MAGIC
# MAGIC Delta (without column mapping) rejects the characters ` ,;{}()\n\t=` in column names. Only if the source headers contain them,
# MAGIC every header is normalized mechanically (ASCII, lowercase, `_`). The original header is kept as the column comment.
# MAGIC These are technical names, not Silver names.

# COMMAND ----------

import re
import unicodedata

DELTA_INVALID_CHARS = set(" ,;{}()\n\t=")


def technical_name(original):
    ascii_name = unicodedata.normalize("NFKD", original).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "_", ascii_name.lower()).strip("_")


rename_required = any(ch in DELTA_INVALID_CHARS for name in source_columns for ch in name)
print("Technical rename required by Delta:", rename_required)

if rename_required:
    column_mapping = [(name, technical_name(name)) for name in source_columns]
else:
    column_mapping = [(name, name) for name in source_columns]

for original, technical in column_mapping:
    print(f"  {original!r:75} -> {technical}")

technical_names = [technical for _, technical in column_mapping]
assert len(set(technical_names)) == len(technical_names), "Technical column names collide"
assert all(technical_names), "Empty technical column name"

bronze_df = source_df.select(
    [
        F.col(f"`{original}`").alias(technical, metadata={"comment": f"Source header: {original}"})
        for original, technical in column_mapping
    ]
).select(
    "*",
    F.lit(SOURCE_DATASET).alias("_source_dataset"),
    F.lit(SOURCE_FILE).alias("_source_file"),
    F.lit(SOURCE_PATH).alias("_source_path"),
    F.lit(SOURCE_YEAR).cast("int").alias("_source_year"),
    F.current_timestamp().alias("_ingested_at_utc"),
)

bronze_df.printSchema()
print("Source columns   :", technical_names)
print("Metadata columns :", METADATA_COLUMNS)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 9. Bronze Data Quality

# COMMAND ----------

bronze_prewrite_count = bronze_df.count()
print("Spark Bronze pre-write row count:", bronze_prewrite_count)

check("DQ-B04", "dataset row count > 0", bronze_prewrite_count > 0, bronze_prewrite_count)

check(
    "DQ-B05",
    "source schema observed and equal to the workbook header row",
    technical_names == EXPECTED_TECHNICAL_COLUMNS,
    technical_names,
)

check(
    "DQ-B06",
    "ingestion metadata columns present",
    all(name in bronze_df.columns for name in METADATA_COLUMNS),
    [name for name in METADATA_COLUMNS if name not in bronze_df.columns],
)

metadata_values = bronze_df.agg(
    F.collect_set("_source_dataset").alias("datasets"),
    F.collect_set("_source_file").alias("files"),
    F.collect_set("_source_year").alias("years"),
).first()

check("DQ-B07", "_source_dataset has one expected value", metadata_values["datasets"] == [SOURCE_DATASET], metadata_values["datasets"])
check("DQ-B08", "_source_file has one expected value", metadata_values["files"] == [SOURCE_FILE], metadata_values["files"])
check("DQ-B09", "_source_year = 2022 for all rows", metadata_values["years"] == [SOURCE_YEAR], metadata_values["years"])

check(
    "DQ-B10",
    "row count preserved from source read to Spark Bronze",
    bronze_prewrite_count == source_parsed_count,
    f"source={source_parsed_count} bronze={bronze_prewrite_count}",
)

# Observations only (not rules): they explain the row count against the local contract (351 rows with pandas).
source_only = bronze_df.select(technical_names)
all_null_rows = source_only.where(F.coalesce(*[F.col(c).cast("string") for c in technical_names]).isNull()).count()
null_first_column = source_only.where(F.col(technical_names[0]).isNull()).count()
print("Observation - fully null source rows:", all_null_rows)
print("Observation - rows with null first column:", null_first_column)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 10. Delta write (managed table, snapshot overwrite)
# MAGIC
# MAGIC No `LOCATION`, no `mergeSchema`, no `overwriteSchema`: a schema change must fail, not evolve silently.

# COMMAND ----------

table_existed_before = spark.catalog.tableExists(TARGET_TABLE)
print("Table existed before this run:", table_existed_before)

(
    bronze_df.write
    .format("delta")
    .mode("overwrite")
    .saveAsTable(TARGET_TABLE)
)
print("Write finished:", TARGET_TABLE)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 11. Post-write validation

# COMMAND ----------

check("DQ-B11", "Bronze table exists", spark.catalog.tableExists(TARGET_TABLE), TARGET_TABLE)

detail = spark.sql(f"DESCRIBE DETAIL {TARGET_TABLE}").first()
print("format   :", detail["format"])
print("location :", detail["location"])
print("numFiles :", detail["numFiles"])
print("properties:", detail["properties"])
check("DQ-B12", "DESCRIBE DETAIL format = delta", detail["format"] == "delta", detail["format"])

delta_postwrite_count = spark.table(TARGET_TABLE).count()
print("Delta Bronze post-write row count:", delta_postwrite_count)
check(
    "DQ-B13",
    "post-write row count equals pre-write row count (no loss, no accumulation)",
    delta_postwrite_count == bronze_prewrite_count,
    f"prewrite={bronze_prewrite_count} postwrite={delta_postwrite_count}",
)

ingestion_timestamps = spark.table(TARGET_TABLE).select("_ingested_at_utc").distinct().count()
check("DQ-B14", "table holds a single ingestion snapshot", ingestion_timestamps == 1, ingestion_timestamps)

spark.sql(f"DESCRIBE TABLE {TARGET_TABLE}").show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 12. Rerun evidence
# MAGIC
# MAGIC Run the whole notebook a second time against the same file. Expected: a new table version, same row count, one ingestion timestamp.
# MAGIC This is a snapshot overwrite, not an incremental load or `MERGE`.

# COMMAND ----------

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

print("Current row count:", delta_postwrite_count)
print("Table existed before this run:", table_existed_before)
print()
print("Bronze checks:")
for check_id, description, status, _ in dq_results:
    print(f"  {status}  {check_id}  {description}")
