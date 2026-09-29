-- P05-B: independent persisted Bronze checks in SQL Warehouse.
-- Run the entire file after initial notebook execution and after its rerun.
-- Preserve every result set. Expected source-body count: 52 each (not 32).
-- File size/SHA identity and XML fidelity are checked by the notebook, not this SQL.
-- Profiles (nulls, duplicates, tokens) are observations, never territorial filters.

SELECT table_name, table_type,
       CASE WHEN table_type = 'MANAGED' THEN 'PASS' ELSE 'FAIL' END AS managed_status
FROM workspace.information_schema.tables
WHERE table_schema = 'bronze'
  AND table_name IN ('sinim_areas_verdes', 'sinim_capacidad_municipal')
ORDER BY table_name;
-- Expect exactly two rows above; absent objects also fail subsequent statements.

-- sinim_areas_verdes: expected 9 ordered columns, 52 rows, no schema mismatches.
DESCRIBE DETAIL workspace.bronze.sinim_areas_verdes;
-- format must equal delta. UC managed status is checked separately above.

WITH expected(column_name, data_type, ordinal_position) AS (
  VALUES ('codigo_comuna', 'STRING', 1),
    ('nombre_comuna', 'STRING', 2),
    ('mmpqc_2024', 'STRING', 3),
    ('mmpzc_2024', 'STRING', 4),
    ('_source_dataset', 'STRING', 5),
    ('_source_file', 'STRING', 6),
    ('_source_path', 'STRING', 7),
    ('_source_year', 'INT', 8),
    ('_ingested_at_utc', 'TIMESTAMP', 9)
), observed AS (
  SELECT column_name, data_type, ordinal_position
  FROM workspace.information_schema.columns
  WHERE table_schema = 'bronze' AND table_name = 'sinim_areas_verdes'
)
SELECT e.column_name AS expected_column, o.column_name AS observed_column,
       e.data_type AS expected_type, o.data_type AS observed_type,
       e.ordinal_position AS expected_position, o.ordinal_position AS observed_position
FROM expected e FULL OUTER JOIN observed o ON e.column_name = o.column_name
WHERE e.column_name IS NULL OR o.column_name IS NULL
   OR e.data_type <> o.data_type OR e.ordinal_position <> o.ordinal_position;
-- Expect zero rows (missing/extra/mistyped/misordered columns).

SELECT COUNT(*) AS row_count,
       CASE WHEN COUNT(*) = 52 THEN 'PASS' ELSE 'FAIL' END AS count_status,
       COUNT(codigo_comuna) AS codes_present,
       COUNT(DISTINCT codigo_comuna) AS distinct_codes
FROM workspace.bronze.sinim_areas_verdes;

SELECT SUM(CASE WHEN codigo_comuna IS NULL THEN 1 ELSE 0 END) AS null_codigo_comuna,
  SUM(CASE WHEN nombre_comuna IS NULL THEN 1 ELSE 0 END) AS null_nombre_comuna,
  SUM(CASE WHEN mmpqc_2024 IS NULL THEN 1 ELSE 0 END) AS null_mmpqc_2024,
  SUM(CASE WHEN mmpzc_2024 IS NULL THEN 1 ELSE 0 END) AS null_mmpzc_2024,
  SUM(CASE WHEN _source_dataset IS NULL THEN 1 ELSE 0 END) AS null__source_dataset,
  SUM(CASE WHEN _source_file IS NULL THEN 1 ELSE 0 END) AS null__source_file,
  SUM(CASE WHEN _source_path IS NULL THEN 1 ELSE 0 END) AS null__source_path,
  SUM(CASE WHEN _source_year IS NULL THEN 1 ELSE 0 END) AS null__source_year,
  SUM(CASE WHEN _ingested_at_utc IS NULL THEN 1 ELSE 0 END) AS null__ingested_at_utc
FROM workspace.bronze.sinim_areas_verdes;
-- Null source fields are diagnostic; metadata nulls must all be zero.

SELECT _source_dataset, _source_file, _source_path, _source_year,
       _ingested_at_utc, COUNT(*) AS row_count
FROM workspace.bronze.sinim_areas_verdes
GROUP BY _source_dataset, _source_file, _source_path, _source_year, _ingested_at_utc;
-- Expect one row with the configured values, a nonnull UTC timestamp, and 52 rows.

SELECT
  SUM(CASE WHEN NOT (_source_dataset <=> 'sinim_areas_verdes')
             OR NOT (_source_file <=> 'datos_municipales_20260402222841_Sin-Corrección-Monetaria.xls')
             OR NOT (_source_path <=> '/Volumes/workspace/bronze/source_files/datos_municipales_20260402222841_Sin-Corrección-Monetaria.xls')
             OR NOT (_source_year <=> 2024)
             OR _ingested_at_utc IS NULL THEN 1 ELSE 0 END) AS invalid_metadata_rows,
  COUNT(DISTINCT _ingested_at_utc) AS snapshot_timestamps
FROM workspace.bronze.sinim_areas_verdes;
-- Expect invalid_metadata_rows = 0 and snapshot_timestamps = 1.

SELECT SUM(CASE WHEN mmpqc_2024 = 'No Aplica' THEN 1 ELSE 0 END) AS mmpqc_2024_no_aplica,
  SUM(CASE WHEN mmpqc_2024 = 'No Recepcionado' THEN 1 ELSE 0 END) AS mmpqc_2024_no_recepcionado,
  SUM(CASE WHEN mmpzc_2024 = 'No Aplica' THEN 1 ELSE 0 END) AS mmpzc_2024_no_aplica,
  SUM(CASE WHEN mmpzc_2024 = 'No Recepcionado' THEN 1 ELSE 0 END) AS mmpzc_2024_no_recepcionado
FROM workspace.bronze.sinim_areas_verdes;
-- A: mmpqc No Aplica=3 / No Recepcionado=2; mmpzc 0 / 2.
-- B: both token counts = 0. Tokens must remain text.

SELECT codigo_comuna, nombre_comuna, mmpqc_2024, mmpzc_2024, COUNT(*) AS occurrences
FROM workspace.bronze.sinim_areas_verdes
GROUP BY codigo_comuna, nombre_comuna, mmpqc_2024, mmpzc_2024
HAVING COUNT(*) > 1;
-- Source-row duplicates are reported, not removed. Current raw: none.

SELECT codigo_comuna, nombre_comuna, mmpqc_2024, mmpzc_2024
FROM workspace.bronze.sinim_areas_verdes
ORDER BY codigo_comuna, nombre_comuna;
-- Inspect all 52 rows. Expected first code 13101, final code 13605.

DESCRIBE HISTORY workspace.bronze.sinim_areas_verdes;
-- On rerun: newer version, 52 rows, overwrite operation, no accumulation.
-- Exact logical equality (excluding _ingested_at_utc) is checked pre-write
-- against the pinned source candidate by the notebook, including duplicates.

-- sinim_capacidad_municipal: expected 8 ordered columns, 52 rows, no schema mismatches.
DESCRIBE DETAIL workspace.bronze.sinim_capacidad_municipal;
-- format must equal delta. UC managed status is checked separately above.

WITH expected(column_name, data_type, ordinal_position) AS (
  VALUES ('codigo_comuna', 'STRING', 1),
    ('nombre_comuna', 'STRING', 2),
    ('iadm41_2024', 'STRING', 3),
    ('_source_dataset', 'STRING', 4),
    ('_source_file', 'STRING', 5),
    ('_source_path', 'STRING', 6),
    ('_source_year', 'INT', 7),
    ('_ingested_at_utc', 'TIMESTAMP', 8)
), observed AS (
  SELECT column_name, data_type, ordinal_position
  FROM workspace.information_schema.columns
  WHERE table_schema = 'bronze' AND table_name = 'sinim_capacidad_municipal'
)
SELECT e.column_name AS expected_column, o.column_name AS observed_column,
       e.data_type AS expected_type, o.data_type AS observed_type,
       e.ordinal_position AS expected_position, o.ordinal_position AS observed_position
FROM expected e FULL OUTER JOIN observed o ON e.column_name = o.column_name
WHERE e.column_name IS NULL OR o.column_name IS NULL
   OR e.data_type <> o.data_type OR e.ordinal_position <> o.ordinal_position;
-- Expect zero rows (missing/extra/mistyped/misordered columns).

SELECT COUNT(*) AS row_count,
       CASE WHEN COUNT(*) = 52 THEN 'PASS' ELSE 'FAIL' END AS count_status,
       COUNT(codigo_comuna) AS codes_present,
       COUNT(DISTINCT codigo_comuna) AS distinct_codes
FROM workspace.bronze.sinim_capacidad_municipal;

SELECT SUM(CASE WHEN codigo_comuna IS NULL THEN 1 ELSE 0 END) AS null_codigo_comuna,
  SUM(CASE WHEN nombre_comuna IS NULL THEN 1 ELSE 0 END) AS null_nombre_comuna,
  SUM(CASE WHEN iadm41_2024 IS NULL THEN 1 ELSE 0 END) AS null_iadm41_2024,
  SUM(CASE WHEN _source_dataset IS NULL THEN 1 ELSE 0 END) AS null__source_dataset,
  SUM(CASE WHEN _source_file IS NULL THEN 1 ELSE 0 END) AS null__source_file,
  SUM(CASE WHEN _source_path IS NULL THEN 1 ELSE 0 END) AS null__source_path,
  SUM(CASE WHEN _source_year IS NULL THEN 1 ELSE 0 END) AS null__source_year,
  SUM(CASE WHEN _ingested_at_utc IS NULL THEN 1 ELSE 0 END) AS null__ingested_at_utc
FROM workspace.bronze.sinim_capacidad_municipal;
-- Null source fields are diagnostic; metadata nulls must all be zero.

SELECT _source_dataset, _source_file, _source_path, _source_year,
       _ingested_at_utc, COUNT(*) AS row_count
FROM workspace.bronze.sinim_capacidad_municipal
GROUP BY _source_dataset, _source_file, _source_path, _source_year, _ingested_at_utc;
-- Expect one row with the configured values, a nonnull UTC timestamp, and 52 rows.

SELECT
  SUM(CASE WHEN NOT (_source_dataset <=> 'sinim_capacidad_municipal')
             OR NOT (_source_file <=> 'datos_municipales_20260402223904_Sin-Corrección-Monetaria.xls')
             OR NOT (_source_path <=> '/Volumes/workspace/bronze/source_files/datos_municipales_20260402223904_Sin-Corrección-Monetaria.xls')
             OR NOT (_source_year <=> 2024)
             OR _ingested_at_utc IS NULL THEN 1 ELSE 0 END) AS invalid_metadata_rows,
  COUNT(DISTINCT _ingested_at_utc) AS snapshot_timestamps
FROM workspace.bronze.sinim_capacidad_municipal;
-- Expect invalid_metadata_rows = 0 and snapshot_timestamps = 1.

SELECT SUM(CASE WHEN iadm41_2024 = 'No Aplica' THEN 1 ELSE 0 END) AS iadm41_2024_no_aplica,
  SUM(CASE WHEN iadm41_2024 = 'No Recepcionado' THEN 1 ELSE 0 END) AS iadm41_2024_no_recepcionado
FROM workspace.bronze.sinim_capacidad_municipal;
-- A: mmpqc No Aplica=3 / No Recepcionado=2; mmpzc 0 / 2.
-- B: both token counts = 0. Tokens must remain text.

SELECT codigo_comuna, nombre_comuna, iadm41_2024, COUNT(*) AS occurrences
FROM workspace.bronze.sinim_capacidad_municipal
GROUP BY codigo_comuna, nombre_comuna, iadm41_2024
HAVING COUNT(*) > 1;
-- Source-row duplicates are reported, not removed. Current raw: none.

SELECT codigo_comuna, nombre_comuna, iadm41_2024
FROM workspace.bronze.sinim_capacidad_municipal
ORDER BY codigo_comuna, nombre_comuna;
-- Inspect all 52 rows. Expected first code 13101, final code 13605.

DESCRIBE HISTORY workspace.bronze.sinim_capacidad_municipal;
-- On rerun: newer version, 52 rows, overwrite operation, no accumulation.
-- Exact logical equality (excluding _ingested_at_utc) is checked pre-write
-- against the pinned source candidate by the notebook, including duplicates.
