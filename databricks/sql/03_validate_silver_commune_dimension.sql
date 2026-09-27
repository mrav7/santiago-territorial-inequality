-- Read-only validation of workspace.silver.dim_comuna after the notebook run.
-- Expected: managed Delta snapshot, five ordered columns, 32 commune rows,
-- exact master-CSV coverage and attributes. Record the latest Delta version
-- before and after a rerun; the later value must be greater.

-- Existence, schema, and physical format.
SHOW TABLES IN workspace.silver;

DESCRIBE TABLE workspace.silver.dim_comuna;

DESCRIBE DETAIL workspace.silver.dim_comuna;

-- Unity Catalog table type: expect exactly one row with table_type = MANAGED.
SELECT table_type
FROM workspace.information_schema.tables
WHERE table_schema = 'silver'
  AND table_name = 'dim_comuna';

SELECT column_name, ordinal_position, full_data_type
FROM workspace.information_schema.columns
WHERE table_schema = 'silver'
  AND table_name = 'dim_comuna'
ORDER BY ordinal_position;

-- Row and key profile: expect 32 rows, 32 distinct non-null keys, no duplicates.
SELECT
  COUNT(*) AS row_count,
  COUNT(DISTINCT codigo_comuna) AS distinct_commune_keys,
  SUM(CASE WHEN codigo_comuna IS NULL THEN 1 ELSE 0 END) AS null_keys
FROM workspace.silver.dim_comuna;

SELECT codigo_comuna, COUNT(*) AS duplicate_count
FROM workspace.silver.dim_comuna
GROUP BY codigo_comuna
HAVING COUNT(*) > 1;

-- Required null and blank profile: all values should be zero.
SELECT
  SUM(CASE WHEN codigo_comuna IS NULL THEN 1 ELSE 0 END) AS null_codigo_comuna,
  SUM(CASE WHEN nombre_comuna IS NULL OR trim(nombre_comuna) = '' THEN 1 ELSE 0 END) AS blank_nombre_comuna,
  SUM(CASE WHEN provincia IS NULL OR trim(provincia) = '' THEN 1 ELSE 0 END) AS blank_provincia,
  SUM(CASE WHEN region IS NULL OR trim(region) = '' THEN 1 ELSE 0 END) AS blank_region,
  SUM(CASE WHEN fuente_referencia IS NULL OR trim(fuente_referencia) = '' THEN 1 ELSE 0 END) AS blank_fuente_referencia,
  COUNT(DISTINCT nombre_comuna) AS distinct_names
FROM workspace.silver.dim_comuna;

-- Expect SANTIAGO = 32 and METROPOLITANA DE SANTIAGO = 32.
SELECT provincia, COUNT(*) AS row_count
FROM workspace.silver.dim_comuna
GROUP BY provincia
ORDER BY provincia;

SELECT region, COUNT(*) AS row_count
FROM workspace.silver.dim_comuna
GROUP BY region
ORDER BY region;

-- Preserve the source reference distribution (the current fixture has A = 32).
SELECT fuente_referencia, COUNT(*) AS row_count
FROM workspace.silver.dim_comuna
GROUP BY fuente_referencia
ORDER BY fuente_referencia;

-- Independent source profile. The file identity check runs in the notebook.
WITH source_rows AS (
  SELECT
    trim(codigo_comuna) AS codigo_text,
    try_cast(trim(codigo_comuna) AS INT) AS codigo_comuna,
    nombre_comuna, provincia, region, fuente_referencia
  FROM read_files(
    '/Volumes/workspace/bronze/source_files/dim_comuna_base.csv',
    format => 'csv',
    header => true,
    schema => 'codigo_comuna STRING, nombre_comuna STRING, provincia STRING, region STRING, fuente_referencia STRING'
  )
)
SELECT
  COUNT(*) AS source_rows,
  COUNT(DISTINCT codigo_comuna) AS distinct_source_keys,
  SUM(CASE WHEN codigo_text IS NULL OR codigo_text = '' THEN 1 ELSE 0 END) AS blank_source_keys,
  SUM(CASE WHEN codigo_text IS NOT NULL AND codigo_text <> '' AND codigo_comuna IS NULL THEN 1 ELSE 0 END) AS uncastable_source_keys
FROM source_rows;

-- Full comparison by canonical INT key: expect 32 matched, no one-sided rows,
-- and zero attribute mismatches. The join does not use the commune name as a key.
WITH source_rows AS (
  SELECT
    try_cast(trim(codigo_comuna) AS INT) AS codigo_comuna,
    nombre_comuna, provincia, region, fuente_referencia
  FROM read_files(
    '/Volumes/workspace/bronze/source_files/dim_comuna_base.csv',
    format => 'csv',
    header => true,
    schema => 'codigo_comuna STRING, nombre_comuna STRING, provincia STRING, region STRING, fuente_referencia STRING'
  )
), comparison AS (
  SELECT
    s.codigo_comuna AS silver_key,
    d.codigo_comuna AS source_key,
    s.nombre_comuna AS silver_name,
    d.nombre_comuna AS source_name,
    s.provincia AS silver_province,
    d.provincia AS source_province,
    s.region AS silver_region,
    d.region AS source_region,
    s.fuente_referencia AS silver_reference,
    d.fuente_referencia AS source_reference
  FROM workspace.silver.dim_comuna AS s
  FULL OUTER JOIN source_rows AS d
    ON s.codigo_comuna = d.codigo_comuna
)
SELECT
  SUM(CASE WHEN silver_key IS NOT NULL AND source_key IS NOT NULL THEN 1 ELSE 0 END) AS matched,
  SUM(CASE WHEN silver_key IS NULL THEN 1 ELSE 0 END) AS source_only,
  SUM(CASE WHEN source_key IS NULL THEN 1 ELSE 0 END) AS silver_only,
  SUM(CASE WHEN silver_key IS NOT NULL AND source_key IS NOT NULL AND NOT (silver_name <=> source_name) THEN 1 ELSE 0 END) AS name_mismatches,
  SUM(CASE WHEN silver_key IS NOT NULL AND source_key IS NOT NULL AND NOT (silver_province <=> source_province) THEN 1 ELSE 0 END) AS province_mismatches,
  SUM(CASE WHEN silver_key IS NOT NULL AND source_key IS NOT NULL AND NOT (silver_region <=> source_region) THEN 1 ELSE 0 END) AS region_mismatches,
  SUM(CASE WHEN silver_key IS NOT NULL AND source_key IS NOT NULL AND NOT (silver_reference <=> source_reference) THEN 1 ELSE 0 END) AS reference_mismatches
FROM comparison;

-- Ordered inspection and Delta history. Compare latest versions across runs.
SELECT codigo_comuna, nombre_comuna, provincia, region, fuente_referencia
FROM workspace.silver.dim_comuna
ORDER BY codigo_comuna;

DESCRIBE HISTORY workspace.silver.dim_comuna;
