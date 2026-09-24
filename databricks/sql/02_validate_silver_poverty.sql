-- 02 · Validate Silver — Poverty by income (Source C)
--
-- Read-only validation of workspace.silver.pobreza_ingresos after running
-- databricks/notebooks/02_silver_poverty.py. Run in the SQL Editor on the
-- Serverless Starter Warehouse. No DDL, no DML.
--
-- Expected:
--   table exists, format = delta
--   row_count = 32, distinct keys = 32, 0 duplicates
--   0 nulls in the four business columns
--   pobreza_ingresos_pct within 0–100
--   anio_pobreza = 2022 for all 32 rows
--   master coverage: 32 matched, 0 missing, 0 extra (requires the dimension in the Volume)
--
-- This SQL complements the notebook checks; it does not replace the pre-write DQ,
-- the file hashes, the 351 → 345 → 32 trace or the key-based baseline equivalence.

-- 1. Existence and physical format
SHOW TABLES IN workspace.silver;

DESCRIBE TABLE workspace.silver.pobreza_ingresos;

DESCRIBE DETAIL workspace.silver.pobreza_ingresos;

-- 2. Schema contract: expected codigo_comuna int, nombre_comuna string,
--    pobreza_ingresos_pct decimal(7,4), anio_pobreza int (in this order)
SELECT column_name, ordinal_position, full_data_type
FROM workspace.information_schema.columns
WHERE table_schema = 'silver'
  AND table_name = 'pobreza_ingresos'
ORDER BY ordinal_position;

-- 3. Row count and key uniqueness
SELECT
  COUNT(*) AS row_count,
  COUNT(DISTINCT codigo_comuna) AS distinct_commune_keys,
  COUNT(*) - COUNT(DISTINCT codigo_comuna) AS duplicate_rows
FROM workspace.silver.pobreza_ingresos;

SELECT codigo_comuna, COUNT(*) AS n
FROM workspace.silver.pobreza_ingresos
GROUP BY codigo_comuna
HAVING COUNT(*) > 1;

-- 4. Nulls in business columns
SELECT
  SUM(CASE WHEN codigo_comuna IS NULL THEN 1 ELSE 0 END) AS null_codigo_comuna,
  SUM(CASE WHEN nombre_comuna IS NULL THEN 1 ELSE 0 END) AS null_nombre_comuna,
  SUM(CASE WHEN pobreza_ingresos_pct IS NULL THEN 1 ELSE 0 END) AS null_pobreza,
  SUM(CASE WHEN anio_pobreza IS NULL THEN 1 ELSE 0 END) AS null_anio
FROM workspace.silver.pobreza_ingresos;

-- 5. Poverty range (percentage, 0–100)
SELECT
  MIN(pobreza_ingresos_pct) AS min_pobreza_pct,
  MAX(pobreza_ingresos_pct) AS max_pobreza_pct,
  SUM(CASE WHEN pobreza_ingresos_pct < 0 OR pobreza_ingresos_pct > 100 THEN 1 ELSE 0 END) AS out_of_range
FROM workspace.silver.pobreza_ingresos;

-- 6. Reference year distribution
SELECT anio_pobreza, COUNT(*) AS n
FROM workspace.silver.pobreza_ingresos
GROUP BY anio_pobreza
ORDER BY anio_pobreza;

-- 7. Master-dimension coverage (read-only file read from the Volume, joined by codigo_comuna)
WITH dim AS (
  SELECT CAST(trim(codigo_comuna) AS INT) AS codigo_comuna
  FROM read_files(
    '/Volumes/workspace/bronze/source_files/dim_comuna_base.csv',
    format => 'csv',
    header => true,
    schema => 'codigo_comuna STRING, nombre_comuna STRING, provincia STRING, region STRING, fuente_referencia STRING'
  )
)
SELECT
  SUM(CASE WHEN s.codigo_comuna IS NOT NULL AND d.codigo_comuna IS NOT NULL THEN 1 ELSE 0 END) AS matched_keys,
  SUM(CASE WHEN s.codigo_comuna IS NULL THEN 1 ELSE 0 END) AS master_keys_missing_in_silver,
  SUM(CASE WHEN d.codigo_comuna IS NULL THEN 1 ELSE 0 END) AS silver_keys_outside_master
FROM workspace.silver.pobreza_ingresos AS s
FULL OUTER JOIN dim AS d
  ON s.codigo_comuna = d.codigo_comuna;

-- 8. Sample, ordered by key
SELECT codigo_comuna, nombre_comuna, pobreza_ingresos_pct, anio_pobreza
FROM workspace.silver.pobreza_ingresos
ORDER BY codigo_comuna;

-- 9. Delta history (diagnostic): expected one WRITE/CREATE per notebook run, 32 output rows
DESCRIBE HISTORY workspace.silver.pobreza_ingresos;
