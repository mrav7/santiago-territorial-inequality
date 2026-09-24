## Objetivo

Construir un pipeline ETL reproducible para analizar **desigualdad territorial en Santiago** combinando:

- areas verdes comunales;
- pobreza por ingresos;
- capacidad municipal;
- poblacion comunal.

## Alcance analitico

- Unidad de analisis final: **una fila = una comuna**
- Cobertura final: **Provincia de Santiago**
- Llave principal obligatoria: **`codigo_comuna`**
- Tipo de analisis: **comparativo y descriptivo, no causal**

`nombre_comuna` se usa solo como apoyo descriptivo y de validacion. La integracion del proyecto se resuelve por `codigo_comuna`, no por nombre crudo.

## Estado real del proyecto

El repositorio contiene dos implementaciones con estados distintos:

- **Implementacion local** (Python + pandas + SQLite): baseline funcional validado.
- **Implementacion Lakehouse** (Databricks + PySpark + Delta Lake + SQL): en construccion por etapas; solo esta validado lo que se indica abajo.

### Implementacion local (baseline validado)

La implementacion local cubre tecnicamente las **Fases 1 a 9**:

1. verificacion estructural y de rutas clave;
2. lectura y perfilado real de las 4 fuentes;
3. validacion de la dimension maestra comunal y homologacion reproducible;
4. extraccion a `staging`;
5. transformacion y validacion de staging por fuente;
6. integracion del dataset final comunal;
7. validacion formal del dataset final;
8. carga final a SQLite y validacion basica de consultas;
9. analisis exploratorio reproducible y generacion de rankings/figuras.

Las **Fases 10, 11 y 12** no forman parte del trabajo tecnico cerrado de este repositorio aun. `docs/informe/` y `docs/presentacion/` se mantienen reservados para esas etapas. El historial Git contiene trabajo de preparacion de materiales de Fase 10 (`docs/informe_lab1_materiales/`, `tools/fase10/`), pero su cierre no esta declarado.

### Implementacion Lakehouse (en construccion)

Arquitectura objetivo: `Fuentes → Bronze → Silver → Gold → Databricks SQL / Power BI`, sobre Databricks Free Edition (compute serverless, objetos managed de Unity Catalog). El detalle y el estado por componente estan en [`docs/architecture/lakehouse.md`](docs/architecture/lakehouse.md).

La numeracion P00–P12 de las etapas Lakehouse es independiente de las Fases 1–12 del pipeline local; no son equivalentes.

| Etapa | Alcance | Estado |
| --- | --- | --- |
| P00 | Auditoria del baseline local | completada; evidencia preservada |
| P01 | Auditoria del entorno Databricks | completada; capacidades del workspace documentadas en la arquitectura |
| P02 | Fundacion Lakehouse (schemas `bronze`/`silver`/`gold`, Volume de landing) | validada |
| P03 | Bronze de pobreza (Fuente C): `workspace.bronze.pobreza_ingresos`, Delta managed, 351 filas, DQ-B01–DQ-B14 en PASS; rerun por snapshot overwrite (no incremental) | validada en Databricks |
| P04 | Silver de pobreza + Data Quality + equivalencia con el baseline | **BLOCKED**: notebook y SQL de validacion implementados, pendientes de ejecucion en Databricks; no existe tabla Silver validada |
| P05–P12 | resto de fuentes, Gold, hardening/SQL serving, orquestacion, cargas incrementales / `MERGE`, schema evolution, Power BI y cierre tecnico | planificadas; no implementadas |

El codigo Lakehouse versionado esta en `databricks/`. El dataset es pequeno: Spark se usa para aprender e implementar patrones de Data Engineering, no por volumen de datos.

## Fuentes versionadas

| ID | Fuente | Archivo real | Referencia |
| --- | --- | --- | --- |
| A | SINIM - Areas Verdes | `data/raw/datos_municipales_20260402222841_Sin-Corrección-Monetaria.xls` | 2024 |
| B | SINIM - Capacidad Municipal | `data/raw/datos_municipales_20260402223904_Sin-Corrección-Monetaria.xls` | 2024 |
| C | Observatorio Social - Pobreza por Ingresos | `data/raw/estimaciones_tasa_pobreza_ingresos_comunas_2022.xlsx` | 2022 |
| D | Censo 2024 - Poblacion Comunal | `data/raw/D1_Poblacion-censada-por-sexo-y-edad-en-grupos-quinquenales.xlsx` | 2024 |

`data/raw/metadata_fuentes.csv` funciona como contrato operativo de lectura y `data/raw/dim_comuna_base.csv` define el universo maestro de 32 comunas.

## Dataset final

El dataset integrado versionado es:

`data/processed/desigualdad_comunal_final.csv`

Estado esperado y validado:

- 32 filas
- 12 columnas
- una fila por comuna
- 32 valores unicos de `codigo_comuna`
- sin duplicados por `codigo_comuna`
- sin valores nulos en las columnas finales
- cobertura exacta del universo maestro de 32 comunas

Columnas:

- `codigo_comuna`
- `nombre_comuna`
- `poblacion`
- `anio_poblacion`
- `pobreza_ingresos_pct`
- `anio_pobreza`
- `areas_verdes_m2`
- `anio_areas_verdes`
- `ipp_miles_pesos`
- `anio_ingresos`
- `areas_verdes_m2_hab`
- `ipp_pesos_hab`

## SQLite

La carga final se materializa en:

`db/lab1_desigualdad.sqlite`

Tablas esperadas:

- `dim_comuna`
- `fact_desigualdad_comunal`
- `metadata_fuentes`

Conteos esperados:

- `dim_comuna`: 32
- `fact_desigualdad_comunal`: 32
- `metadata_fuentes`: 4

El diseno sigue una logica dimension-hecho: `nombre_comuna` vive en `dim_comuna`; la fact table no replica esa columna.

## Ejecucion

Se recomienda ejecutar el pipeline en un entorno virtual aislado. `requirements.txt` actualmente no fija versiones, por lo que la reproducibilidad exacta del entorno queda pendiente de una validacion especifica de dependencias.

Ejemplo:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Ejecucion del pipeline completo desde la raiz del repositorio:

```bash
python src/main.py
```

Tambien soporta ejecucion como modulo:

```bash
python -m src.main
```

Ambos comandos recorren Fases 1 a 9 y regeneran los artefactos del pipeline. La escritura de `outputs/perfilado_fuentes.xlsx` y `db/lab1_desigualdad.sqlite` evita reserializaciones innecesarias cuando el contenido ya coincide con el estado esperado.

## Estructura principal

```text
santiago-territorial-inequality/
├── data/
│   ├── raw/
│   ├── staging/
│   └── processed/
├── databricks/                 # implementacion Lakehouse
│   ├── notebooks/              # 01_bronze_poverty.py, 02_silver_poverty.py
│   └── sql/                    # 00_foundation.sql, 01_validate_bronze_poverty.sql, 02_validate_silver_poverty.sql
├── db/
├── docs/
│   ├── architecture/           # lakehouse.md
│   ├── informe/
│   ├── informe_lab1_materiales/
│   └── presentacion/
├── notebooks/
├── outputs/
│   └── figures/
├── src/
│   ├── __init__.py
│   ├── analyze.py
│   ├── comunas.py
│   ├── config.py
│   ├── extract.py
│   ├── integrate.py
│   ├── load.py
│   ├── main.py
│   ├── transform.py
│   └── validate.py
├── tools/
│   └── fase10/
├── README.md
└── requirements.txt
```

## Artefactos relevantes

Outputs operativos y de validacion:

- `outputs/perfilado_fuentes.xlsx`
- `outputs/conflictos_fuentes.md`
- `outputs/homologacion_comunas.csv`
- `outputs/resumen_homologacion.md`
- `outputs/resumen_transformaciones.md`
- `outputs/validacion_staging.csv`
- `outputs/log_integracion.md`
- `outputs/resumen_dataset_final.md`
- `outputs/reporte_validacion_final.csv`
- `outputs/reporte_validacion_final.md`
- `outputs/reporte_carga_sqlite.md`
- `outputs/reporte_consultas_sqlite.csv`

Outputs analiticos de Fase 9:

- `outputs/analisis_exploratorio.md`
- `outputs/tablas_hallazgos_fase9.csv`
- `outputs/ranking_areas_verdes.csv`
- `outputs/ranking_pobreza.csv`
- `outputs/ranking_ipp.csv`
- `outputs/indice_rezago_territorial.csv`
- figuras en `outputs/figures/`

## Limitaciones metodologicas minimas

- El analisis se restringe a la Provincia de Santiago.
- Las fuentes combinan anos de referencia distintos: pobreza 2022 y las demas variables 2024. No se homogenizan.
- El objetivo es comparativo y descriptivo; no se infieren relaciones causales.
- Los archivos `data/raw/` son insumos versionados y no deben alterarse manualmente.
