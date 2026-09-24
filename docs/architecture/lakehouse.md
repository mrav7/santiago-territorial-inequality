# Arquitectura Lakehouse

Este documento describe la segunda implementación del proyecto: una versión Lakehouse (Medallion) sobre Databricks. La implementación local existente no se reemplaza. Sigue siendo la referencia funcional contra la que se valida la versión Lakehouse.

La §10 registra el estado real de cada componente. Todo lo que no figure ahí como `IMPLEMENTED` o `VALIDATED` es diseño, no implementación.

## 1. Dos implementaciones

| | Local (baseline) | Lakehouse (objetivo) |
|---|---|---|
| Tecnologías | Python + pandas + SQLite | Databricks + PySpark + Delta Lake + SQL |
| Entrada | `data/raw/` (CSV, XLS SpreadsheetML, XLSX) | los mismos archivos, aterrizados en un Volume de Unity Catalog |
| Producto | `data/processed/desigualdad_comunal_final.csv` y `db/lab1_desigualdad.sqlite` | tablas Delta en `workspace.gold` |
| Estado | implementado y validado (Fases 1–9) | fundación creada; Bronze y Silver de la Fuente C validados; resto de fuentes y Gold no implementados; ver §10 |
| Ejecución | `python -m src.main` | Databricks Free Edition, compute serverless |

El dataset es pequeño: 32 comunas y cuatro fuentes. Spark no se usa por volumen de datos. Se usa para aprender e implementar patrones de Data Engineering transferibles: DataFrames con schemas explícitos, Delta, calidad de datos y orquestación.

## 2. Flujo

```text
Archivos fuente locales (data/raw/)
        │  upload explícito, por fuente, en cada fase de ingestión
        ▼
UC managed Volume  workspace.bronze.source_files
        ▼
Bronze Delta       workspace.bronze.*
        ▼
Silver Delta       workspace.silver.*
        ▼
Data Quality
        ▼
Gold Delta         workspace.gold.*
        ▼
Databricks SQL (Serverless Starter Warehouse)
        ▼
Power BI (planned)
```

No se usan Kafka, streaming, Airflow, dbt, Terraform, Kubernetes, ADF ni MLflow. Ningún problema actual del proyecto los requiere.

## 3. Namespace (Unity Catalog)

| Objeto | Tipo | Propósito |
|---|---|---|
| `workspace` | catálogo existente | catálogo del workspace; no se crea uno nuevo |
| `workspace.bronze` | schema | ingestión cercana al origen y landing |
| `workspace.silver` | schema | datasets tipados, limpios y con llave comunal resuelta |
| `workspace.gold` | schema | modelo analítico y serving |
| `workspace.bronze.source_files` | managed Volume | landing de archivos fuente: `/Volumes/workspace/bronze/source_files/` |

El DDL reproducible está en [`databricks/sql/00_foundation.sql`](../../databricks/sql/00_foundation.sql). Solo crea schemas y el Volume. `IF NOT EXISTS` permite reejecutarlo sin error. No es una forma de incrementalidad del pipeline.

Configuración estable, documentada aquí mientras no haya repetición que justifique extraerla a código:

```text
catalog        = workspace
bronze_schema  = bronze
silver_schema  = silver
gold_schema    = gold
landing_volume = source_files
```

**Convención de nombres:** minúsculas, `snake_case`, nombres descriptivos y namespace `catalog.schema.object`. Nombres previstos (las tablas `bronze` y `silver` de `pobreza_ingresos` ya existen, ver §10; las `gold` son diseño, no objetos existentes):

- `workspace.bronze.pobreza_ingresos`
- `workspace.silver.pobreza_ingresos`
- `workspace.gold.dim_comuna`
- `workspace.gold.fact_desigualdad_comunal`
- `workspace.gold.metadata_fuentes`

## 4. Responsabilidad por capa

### Bronze

- Ingestión y trazabilidad.
- Estructura cercana al origen, con valores crudos o casi crudos y el schema observado.
- Transformación mínima: sin limpieza de negocio ni eliminación silenciosa de filas.
- Metadata de ingestión propuesta:

  | Columna | Contenido |
  |---|---|
  | `_source_dataset` | identificador del dataset (p. ej. `pobreza_ingresos`) |
  | `_source_file` | nombre del archivo |
  | `_source_path` | ruta en el Volume |
  | `_source_year` | año de referencia de la fuente |
  | `_ingested_at_utc` | timestamp de ingestión |

  No se incluyen `batch_id`, watermarks, `merge_key` ni `change_type` hasta que la incrementalidad los necesite. La primera ingestión real confirmará si cada columna aporta valor.

### Silver

- Nombres estables y tipado.
- Limpieza y normalización.
- Homologación comunal y resolución de `codigo_comuna`.
- Deduplicación justificada.
- Reglas de calidad.

### Gold

- Integración analítica en una fila por comuna.
- Modelo dimensión-hecho equivalente al baseline: `dim_comuna`, `fact_desigualdad_comunal`, `metadata_fuentes`.
- KPIs y derivadas (`areas_verdes_m2_hab`, `ipp_pesos_hab`).
- Serving vía Databricks SQL.

Solo se agregan tablas Gold con un propósito analítico o de serving concreto.

## 5. Invariantes de dominio

Las mismas que en la implementación local:

- **Grano final:** una fila = una comuna.
- **Universo:** Provincia de Santiago, 32 comunas (`data/raw/dim_comuna_base.csv`).
- **Llave canónica:** `codigo_comuna`. `nombre_comuna` sirve para descripción, depuración y detección de conflictos. No es llave de integración ni reemplaza joins por código.
- **Años de referencia distintos y visibles:** pobreza 2022; población, áreas verdes y capacidad municipal 2024. No se homogenizan.
- **Análisis descriptivo y comparativo, no causal.**
- **Outlier de Quilicura:** el valor alto de `areas_verdes_m2_hab` se conserva como outlier plausible, sin tratamiento.

## 6. Cómputo y almacenamiento

- **Cómputo:** serverless. Es la única modalidad disponible en Databricks Free Edition. El DDL y las consultas SQL usan el único SQL Warehouse existente (Serverless Starter Warehouse, 2X-Small).
- **Almacenamiento:** objetos *managed* de Unity Catalog (schemas, Volume y, más adelante, tablas).
  - No se diseña sobre external locations, storage credentials, external tables ni storage cloud propio.
  - No hacen falta para el proyecto y su disponibilidad no está verificada.
  - El cloud/provider del workspace tampoco está verificado. Una solución managed evita depender de él.
- **Fuentes:** se aterrizan desde los archivos versionados del repositorio y no se descargan desde las URLs originales. Así la entrada es la misma que usa el baseline local.

## 7. Organización de código

- **Notebook:** coordinación, exploración y ejecución visible por etapa. No se construye un notebook monolítico: se separa por capa y propósito.
- **Módulo reutilizable:** solo para lógica repetida entre fuentes o suficientemente estable. No se extrae cada transformación de forma prematura.
- **SQL:** DDL, joins analíticos, modelos Gold, consultas de validación y serving, cuando sea más claro que PySpark.
- **PySpark:** ingestión, parsing, limpieza y lógica de calidad reutilizable.
  - Se usa con conciencia de schemas explícitos, lazy evaluation, transformaciones vs. acciones, joins, shuffles y particiones.
  - No es una traducción línea a línea del código pandas.

`databricks/notebooks/` contiene el vertical Bronze de la Fuente C (`01_bronze_poverty.py`) y el Silver de la Fuente C (`02_silver_poverty.py`, ejecutado y validado el 2026-09-24). `databricks/src/` se creará solo cuando exista lógica reutilizable real.

## 8. Data Quality por capa

| Capa | Contrato mínimo |
|---|---|
| Bronze | lectura exitosa; dataset no vacío; fuente identificada; schema observado registrado; metadata de ingestión presente |
| Silver | `codigo_comuna` completo; tipos esperados; nulls; duplicados; códigos desconocidos; rangos; año de referencia; cobertura territorial |
| Gold | 32 comunas; una fila por `codigo_comuna`; integridad de joins; cero extras; cero faltantes; años visibles; métricas válidas |

Las validaciones se implementan con cada capa. Por ahora no se construye un framework genérico de calidad.

## 9. Equivalencia con el baseline local

El pipeline local es la referencia funcional. La equivalencia se evalúa de forma progresiva:

1. **Primera fuente (pobreza, Fuente C):** Silver Lakehouse vs. `data/staging/pobreza_staging.csv`, o el resultado local equivalente.
2. **Producto final:** Gold Lakehouse vs. `data/processed/desigualdad_comunal_final.csv` y `db/lab1_desigualdad.sqlite`.

Qué se compara, según corresponda:

- conteo de filas y columnas;
- conjunto de `codigo_comuna`, con llaves faltantes y extra;
- nulls y duplicados;
- años de referencia;
- valores analíticos, con tolerancias numéricas explícitas.

"Se ven parecidos" no cuenta como equivalencia. Toda diferencia material se investiga y se documenta. Una diferencia no es automáticamente un defecto, pero tampoco se oculta cambiando la metodología.

## 10. Estado de implementación

Estados: `IMPLEMENTED` (existe en el repositorio o en el workspace), `VALIDATED` (verificado con evidencia de ejecución), `PLANNED` (diseño), `BLOCKED` (etapa detenida por una condición pendiente que impide continuar o validar su gate), `NOT VERIFIED` (capacidad de plataforma sin confirmar).

| Componente | Estado |
|---|---|
| Pipeline local (Fases 1–9) | VALIDATED |
| Diseño de namespace y capas (este documento) | IMPLEMENTED |
| DDL de fundación (`databricks/sql/00_foundation.sql`) | VALIDATED: ejecutado manualmente en SQL Editor (Serverless Starter Warehouse) el 2026-09-23 |
| Schemas `workspace.bronze` / `silver` / `gold` | VALIDATED: existen (`SHOW SCHEMAS`, `DESCRIBE SCHEMA EXTENDED`) |
| Volume `workspace.bronze.source_files` | VALIDATED: existe, `volume_type = MANAGED` (`SHOW VOLUMES`, `DESCRIBE VOLUME`) |
| Aterrizaje de la Fuente C en el Volume | VALIDATED: archivo versionado subido; tamaño y SHA-256 verificados desde el notebook (DQ-B02) |
| Bronze Fuente C `workspace.bronze.pobreza_ingresos` | VALIDATED: tabla managed Delta, 351 filas, metadata de ingestión, checks Bronze DQ-B01…B14 en PASS (`databricks/notebooks/01_bronze_poverty.py`, `databricks/sql/01_validate_bronze_poverty.sql`) |
| Rerun Bronze (snapshot overwrite) | VALIDATED: segunda ejecución crea la versión 1, mantiene 351 filas, sin acumulación; no es carga incremental |
| Rerun / idempotencia Silver | NOT VALIDATED: solo existe la ejecución inicial (versión 0) |
| Lector Excel nativo disponible en Databricks vía Spark (`spark.read.format("excel")`) | VALIDATED en serverless: `listSheets` y lectura de `Estimaciones!A3:J354`; decodificación Python de borde no usada |
| Silver Fuente C `workspace.silver.pobreza_ingresos` (P04) | VALIDATED: `databricks/notebooks/02_silver_poverty.py` ejecutado con Run all una vez el 2026-09-24 (compute serverless; target inexistente antes de la ejecución). Bronze 351 → 345 filas con código comunal válido (`^[0-9]{4,5}$`: 206 de 4 dígitos, 139 de 5) + 6 no comunales → join por `codigo_comuna` con `dim_comuna_base.csv` → 32 filas (313 códigos fuera del universo; 0 claves maestras faltantes). Tabla managed Delta, no temporal; schema `codigo_comuna INT`, `nombre_comuna STRING`, `pobreza_ingresos_pct DECIMAL(7,4)`, `anio_pobreza INT`; `DESCRIBE HISTORY` solo con la versión 0 (creación inicial) |
| Data Quality Silver de la Fuente C (P04) | VALIDATED: DQ-S01…S26 en PASS en el notebook; `databricks/sql/02_validate_silver_poverty.sql` ejecutado completo en SQL Editor (Serverless Starter Warehouse, 12 result sets): 32 filas, 32 claves distintas, 0 duplicados, 0 nulls por columna, pct entre 0.8910 y 9.2938 (0 fuera de rango), `anio_pobreza` = 2022 en las 32 filas, cobertura exacta de la dimensión (32 coincidencias, 0 faltantes, 0 extras) |
| Equivalencia Silver pobreza vs. baseline local (P04) | VALIDATED: EQ-S01…S10 en PASS contra `pobreza_staging.csv` y `desigualdad_comunal_final.csv`; tolerancia `1e-9`, `max_abs_diff` = 0 |
| Silver del resto de fuentes | PLANNED |
| Gold y Data Quality Gold | PLANNED |
| Equivalencia del producto final (Gold) con el baseline | PLANNED |
| Orquestación (Databricks Jobs) | PLANNED |
| Cargas incrementales / `MERGE` | PLANNED |
| Schema enforcement / evolution | PLANNED |
| Serving en Power BI | PLANNED |
| PySpark en ejecución en el workspace | VALIDATED para Bronze y Silver de la Fuente C: DataFrames, joins, acciones, metadata y escritura Delta ejecutadas por los notebooks |
| Delta Lake en ejecución en el workspace | VALIDATED para Bronze (`DESCRIBE DETAIL` format `delta`; `DESCRIBE HISTORY` con versiones 0 y 1) y Silver de la Fuente C (format `delta`; versión 0). Gold sin validar |
| Spark / Python del compute serverless | VALIDATED: Spark 4.2.0, Python 3.12.3 (ejecución del 2026-09-23) |
| Environment version | NOT VERIFIED (no se registró en la UI) |
| External locations / storage credentials | NOT VERIFIED (no requeridas) |
