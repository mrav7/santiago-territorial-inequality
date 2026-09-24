-- Santiago Territorial Inequality - Lakehouse foundation
--
-- Creates the Unity Catalog namespace (Bronze / Silver / Gold schemas) and the
-- managed landing Volume inside the existing `workspace` catalog.
--
-- Scope: infrastructure DDL only. No tables, no data, no external storage.
-- Target: Databricks SQL Editor on the existing Serverless Starter Warehouse.
--
-- IF NOT EXISTS makes a rerun safe, but it also succeeds silently when an
-- object already exists. Check for pre-existing objects before the first run:
--
--   SHOW SCHEMAS IN workspace;
--   SHOW VOLUMES IN workspace.bronze;   -- only if `bronze` already exists
--
-- Validate after running:
--
--   SHOW SCHEMAS IN workspace;
--   SHOW VOLUMES IN workspace.bronze;
--   DESCRIBE VOLUME workspace.bronze.source_files;

CREATE SCHEMA IF NOT EXISTS workspace.bronze
COMMENT 'Bronze: source-aligned ingestion layer and landing assets (Santiago Territorial Inequality)';

CREATE SCHEMA IF NOT EXISTS workspace.silver
COMMENT 'Silver: typed, cleaned, commune-key resolved and quality-controlled datasets (Santiago Territorial Inequality)';

CREATE SCHEMA IF NOT EXISTS workspace.gold
COMMENT 'Gold: analytics-ready dimensional and serving layer (Santiago Territorial Inequality)';

-- No LOCATION clause: this is a managed Volume.
-- Path: /Volumes/workspace/bronze/source_files/
CREATE VOLUME IF NOT EXISTS workspace.bronze.source_files
COMMENT 'Managed landing volume for source files of the Santiago Territorial Inequality project';
