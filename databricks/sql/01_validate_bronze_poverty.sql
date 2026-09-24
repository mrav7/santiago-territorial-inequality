-- Santiago Territorial Inequality - Bronze poverty validation (Source C)
--
-- Read-only checks for workspace.bronze.pobreza_ingresos, written by
-- databricks/notebooks/01_bronze_poverty.py.
-- Run in the SQL Editor (Serverless Starter Warehouse) after each notebook run.

-- Table exists in Bronze.
SHOW TABLES IN workspace.bronze;

-- Columns, types and source-header comments.
DESCRIBE TABLE workspace.bronze.pobreza_ingresos;

-- Expected: format = delta, managed location, no user-specified LOCATION.
DESCRIBE DETAIL workspace.bronze.pobreza_ingresos;

-- Expected: > 0, and unchanged after a rerun.
SELECT COUNT(*) AS row_count
FROM workspace.bronze.pobreza_ingresos;

-- Expected: one row (pobreza_ingresos, the source file, 2022).
SELECT
  _source_dataset,
  _source_file,
  _source_path,
  _source_year,
  COUNT(*) AS row_count
FROM workspace.bronze.pobreza_ingresos
GROUP BY
  _source_dataset,
  _source_file,
  _source_path,
  _source_year;

-- Expected: 1. A rerun replaces the snapshot instead of appending a second one.
SELECT
  COUNT(DISTINCT _ingested_at_utc) AS ingestion_snapshots,
  MIN(_ingested_at_utc) AS ingested_at_utc
FROM workspace.bronze.pobreza_ingresos;

-- Delta transaction log: one version per notebook run.
DESCRIBE HISTORY workspace.bronze.pobreza_ingresos;
