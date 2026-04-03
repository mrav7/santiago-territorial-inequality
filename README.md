# lab1-bi-1s2026

Repositorio del **Lab 1 - Proceso ETL** del curso **Inteligencia de Negocios**.

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

El repositorio ya implementa tecnicamente las **Fases 1 a 9**:

1. verificacion estructural y de rutas clave;
2. lectura y perfilado real de las 4 fuentes;
3. validacion de la dimension maestra comunal y homologacion reproducible;
4. extraccion a `staging`;
5. transformacion y validacion de staging por fuente;
6. integracion del dataset final comunal;
7. validacion formal del dataset final;
8. carga final a SQLite y validacion basica de consultas;
9. analisis exploratorio reproducible y generacion de rankings/figuras.

Las **Fases 10, 11 y 12** no forman parte del trabajo tecnico cerrado de este repositorio aun. `docs/informe/` y `docs/presentacion/` se mantienen reservados para esas etapas.

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
- sin duplicados por `codigo_comuna`

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

Instalacion de dependencias:

```bash
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
lab1-bi-1s2026/
├── data/
│   ├── raw/
│   ├── staging/
│   └── processed/
├── db/
├── docs/
│   ├── informe/
│   └── presentacion/
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
- Las fuentes combinan anos de referencia distintos: pobreza 2022 y las demas variables 2024.
- El objetivo es comparativo y descriptivo; no se infieren relaciones causales.
- Los archivos `data/raw/` son insumos versionados y no deben alterarse manualmente.
