# R00 — Baseline Local Audit

**Prompt:** P00 — Baseline Local Audit
**Fecha de ejecución:** 2026-09-23
**Agente:** Claude Code (Opus 5.5)
**Branch:** `chore/p00-baseline-local-audit` (creada desde `main`, sin commits)

---

## 1. Executive summary

El pipeline local (Fases 1–9) se ejecutó con `python -m src.main` y terminó con exit code 0 sin salida en stderr. Los productos resultantes se verificaron directamente, sin depender de los mensajes de consola del pipeline:

- `data/processed/desigualdad_comunal_final.csv`: 32 filas, 12 columnas en el orden esperado, `codigo_comuna` sin nulls ni duplicados, cobertura exacta de `dim_comuna_base.csv` (`missing_codes=[]`, `extra_codes=[]`), 0 nulls en todas las columnas y años 2024/2022/2024/2024.
- `db/lab1_desigualdad.sqlite`: `quick_check=ok`, tablas 32/32/4, sin duplicados de llave, cobertura dim/fact exacta.
- CSV ↔ SQLite (`dim_comuna ⋈ fact_desigualdad_comunal`): igualdad **exacta** en las 32 llaves y en las 11 columnas no clave.
- Una regeneración completa desde cero en una copia aislada (`git archive HEAD`) produjo CSV/MD byte-idénticos, y SQLite y XLSX semánticamente idénticos.
- Un segundo rerun inmediato no produjo cambios adicionales.

La única diferencia en Git corresponde a las 5 figuras PNG de `outputs/figures/`. Tienen las mismas dimensiones y el mismo contenido visual; la diferencia viene del renderizado de fuentes y antialiasing de la versión de matplotlib instalada ahora. No es una diferencia semántica.

Estado final: **PASS**. Recomendación: **APPROVE P01**, con los issues de la §18 registrados para trabajo posterior.

## 2. Final status

**PASS**

## 3. Git baseline

| Ítem | Valor |
|---|---|
| Branch inicial | `main` |
| HEAD | `e5a4dbfc4e1af54c863f1ff56dccdb3b1ff47ab8` (`chore: ai docs adjustment`) |
| `git status --short` inicial | vacío (working tree limpio) |
| Archivos modificados preexistentes | ninguno |
| Untracked preexistentes | ninguno |
| Acción | `git switch -c chore/p00-baseline-local-audit` (autorizado por P00 §5.1) |
| Remote | `origin git@github.com:mrav7/santiago-territorial-inequality-etl.git` (no se usó) |

## 4. Repository state

**Estructura relevante observada:** `src/` (10 módulos, 5433 líneas en total), `data/{raw,staging,processed}`, `db/`, `outputs/` + `outputs/figures/`, `docs/{informe,informe_lab1_materiales,presentacion}`, `tools/fase10/preparar_materiales.py`, `notebooks/` (solo `.gitkeep`), `AGENTS.md`, `CLAUDE.md`, `README.md`, `requirements.txt`, `.gitignore`. Hay 106 archivos trackeados.

| Elemento | Estado |
|---|---|
| `AGENTS.md` / `CLAUDE.md` | ambos existen, 18479 bytes cada uno; `cmp` exit 0 → **idénticos** |
| `tests/` | no existe |
| `pyproject.toml`, `pytest.ini`, `setup.cfg` | no existen |
| `.github/workflows/` | no existe (tampoco `.github/`) |
| Linters / type checking (ruff, flake8, mypy, pre-commit, tox, Makefile) | ninguna configuración encontrada |
| `docs/architecture/lakehouse.md` | no existe |
| `docs/ai/` | no existía; se creó solo `docs/ai/reports/` para este R00 |

**Evidencia automatizada existente:** no hay suite de tests ni CI. La única evidencia automatizada es la validación ejecutable embebida en el propio pipeline:

- preflight de Fase 1 en `src/main.py`;
- checks de la dimensión en `src/comunas.py`;
- validación de staging y del dataset final en `src/validate.py`;
- `raise ValueError` de integridad en `src/integrate.py` y `src/load.py`;
- chequeo de consistencia CSV/SQLite en `src/analyze.py`.

Esos checks escriben reportes en `outputs/`.

## 5. Runtime

| Ítem | Valor |
|---|---|
| Intérprete del sistema | `/usr/bin/python`, Python 3.14.7 (Fedora, Linux 7.2.7) |
| pip en el intérprete del sistema | **no disponible** (`/usr/bin/python: No module named pip`) |
| Dependencias en el intérprete del sistema | numpy 2.4.6; pandas, openpyxl, matplotlib y jupyter **no instalados** |
| Entorno usado para ejecutar | venv aislado fuera del repo (scratchpad de sesión), Python 3.14.7 |
| Comando de instalación | `<venv>/bin/python -m pip install -r requirements.txt` → exit 0 |

Versiones instaladas en el venv (`requirements.txt` no fija versiones):

| Paquete | Versión |
|---|---|
| pandas | 3.0.6 |
| openpyxl | 3.1.5 |
| numpy | 2.5.3 |
| matplotlib | 3.11.2 |
| jupyter | 1.1.1 (notebook 7.6.3, jupyterlab 4.6.4, ipykernel 7.3.0) |
| sqlite3 (biblioteca de Python) | 3.51.2 |

No se modificó `requirements.txt` y no se agregaron dependencias. El uso del venv es una desviación que se detalla en la §17.

## 6. Source inventory

La fuente de verdad es `src/config.py` (`RAW_SOURCES`) contrastado con `data/raw/metadata_fuentes.csv`. Además se verificó el formato real de cada archivo con `file` y con su cabecera.

| ID | Institución / nombre | Archivo | Formato declarado | Formato observado | Año ref. | Existe | Estrategia de lectura (código) |
|---|---|---|---|---|---|---|---|
| A | SINIM – Áreas Verdes | `datos_municipales_20260402222841_Sin-Corrección-Monetaria.xls` | xls (SpreadsheetML/XML Excel 2003) | texto UTF-8 que empieza con `<?xml version="1.0"?>` y `<?mso-application progid="Excel.Sheet"?>` | 2024 | sí | parser XML propio (`extract.py:201` `_extract_spreadsheetml_matrix`, `ElementTree`, namespace `urn:schemas-microsoft-com:office:spreadsheet`), Hoja1, skiprows=2 |
| B | SINIM – Capacidad Municipal | `datos_municipales_20260402223904_Sin-Corrección-Monetaria.xls` | ídem | ídem | 2024 | sí | ídem |
| C | Observatorio Social / MDSF – Pobreza por Ingresos | `estimaciones_tasa_pobreza_ingresos_comunas_2022.xlsx` | xlsx | Microsoft Excel 2007+ | 2022 | sí | `pandas.read_excel`, hoja `Estimaciones`, skiprows=2 |
| D | INE – Censo 2024 Población Comunal | `D1_Poblacion-censada-por-sexo-y-edad-en-grupos-quinquenales.xlsx` | xlsx | Microsoft Excel 2007+ | 2024 | sí | `pandas.read_excel`, hoja `2`, skiprows=3 |

**SINIM (A, B):** `extract.py:334-339` (`read_source`) despacha a `_read_spreadsheetml_source` cuando `contract.uses_spreadsheetml`. En la ejecución real, stdout reporta `parser=spreadsheetml_xml_2003` para A y B y `parser=pandas_read_excel` para C y D. Esto confirma que A y B no se leen con `pandas.read_excel()` directo.

**Metadata:** `data/raw/metadata_fuentes.csv` tiene 4 filas (A–D) y las 13 columnas de `METADATA_REQUIRED_COLUMNS`. El preflight valida archivo, hoja y skiprows contra `config.py`; las 4 fuentes resultaron consistentes.

**Dimensión maestra (`data/raw/dim_comuna_base.csv`):**

- 32 filas;
- columnas `codigo_comuna, nombre_comuna, provincia, region, fuente_referencia`, que coinciden con `DIM_COMUNA_BASE_REQUIRED_COLUMNS`;
- `codigo_comuna`: 0 nulls, 0 duplicados, rango 13101–13132;
- `nombre_comuna`: 0 duplicados;
- `provincia`: `SANTIAGO` (valor único);
- `region`: `METROPOLITANA DE SANTIAGO` (valor único);
- `fuente_referencia`: `A` (valor único).

**`codigo_comuna` como llave central (evidencia en código):**

- `comunas.py:268-282`: el merge es `on="codigo_comuna"`, y stdout declara la política: "La llave principal del proyecto es `codigo_comuna` … no deben hacerse joins futuros por nombre crudo".
- `transform.py:96-104`: el merge es sobre `codigo_comuna_num`, y el nombre final se toma de la dimensión (`nombre_comuna_estandar`), no de la fuente.
- `integrate.py:229-232`: merges `on="codigo_comuna", how="left"`.
- `load.py`: PK `codigo_comuna` en dim y fact, con FK de fact hacia dim.

No se encontraron joins por nombre crudo.

## 7. Pipeline execution

| Ítem | Valor |
|---|---|
| Comando | `python -m src.main` (con el intérprete del venv; `MPLBACKEND=Agg` en el entorno, redundante porque `analyze.py:12` ya fija `matplotlib.use("Agg")`) |
| Exit code | **0** |
| stderr | vacío (0 bytes) |
| stdout | 168 líneas |
| Duración | ~2.6 s |

**Resultado por fase (según stdout, verificado después con las mediciones de las §8–§11):**

| Fase | Resultado reportado |
|---|---|
| 1 Preflight | 11 directorios, 8 rutas clave, dim y metadata: todo `[OK]` |
| 2 Perfilado | A 52×4, B 52×3 (spreadsheetml); C 351×10, D 349×10 (read_excel); las 4 cubren las 32 comunas objetivo |
| 3 Llave maestra | dim con 32 comunas, código y nombre únicos, provincia y región coherentes. Homologación: A y B con 26 exactas + 6 por normalización; C y D con 0 exactas + 32 por normalización; 0 manuales |
| 4–5 Staging | A 32×5, B 32×3, C 32×3, D 32×3; validación `[OK]` |
| 6 Integración | merges D→C→A→B, siempre 32→32 filas; dataset final 32×12 |
| 7 Validación final | 17 checks `[OK]`, `apto_para_sqlite: APTO` |
| 8 SQLite | 32/32/4; `fact_sin_dim=0`, `dim_sin_fact=0` |
| 9 Análisis | consistencia CSV/SQLite 32/32 sin llaves huérfanas; 7 comunas rezagadas en ≥2 dimensiones |

## 8. Final dataset baseline

Medición directa con pandas sobre `data/processed/desigualdad_comunal_final.csv`, leyendo `codigo_comuna` como string.

| Propiedad | Observado |
|---|---|
| Filas | 32 |
| Columnas | 12 |
| Orden de columnas | idéntico al esperado (`codigo_comuna, nombre_comuna, poblacion, anio_poblacion, pobreza_ingresos_pct, anio_pobreza, areas_verdes_m2, anio_areas_verdes, ipp_miles_pesos, anio_ingresos, areas_verdes_m2_hab, ipp_pesos_hab`) |
| dtypes inferidos | `codigo_comuna`/`nombre_comuna` str; `poblacion`, `anio_*`, `areas_verdes_m2`, `ipp_miles_pesos` int64; `pobreza_ingresos_pct`, `areas_verdes_m2_hab`, `ipp_pesos_hab` float64 |
| Key nulls / duplicados / únicos | 0 / 0 / 32 |
| Formato de la llave | 5 dígitos, patrón `13\d{3}`: sí en los 32 casos |
| `missing_codes` | `[]` |
| `extra_codes` | `[]` |
| `nombre_comuna` = nombre de la dim (por código) | sí, 32/32 |
| Nulls por columna | 0 en las 12 columnas |
| `anio_poblacion` | `[2024]` |
| `anio_pobreza` | `[2022]` |
| `anio_areas_verdes` | `[2024]` |
| `anio_ingresos` | `[2024]` |

**Métricas descriptivas (evidencia de baseline, sin reinterpretación):**

| Métrica | Mínimo | Máximo |
|---|---|---|
| `poblacion` | 76002 (SAN RAMON) | 503635 (MAIPU) |
| `pobreza_ingresos_pct` | 0.891 (VITACURA) | 9.2938 (LA PINTANA) |
| `areas_verdes_m2` | 73347 (CONCHALI) | 808434356 (QUILICURA) |
| `ipp_miles_pesos` | 3525077 (CERRO NAVIA) | 220242010 (LAS CONDES) |
| `areas_verdes_m2_hab` | 0.603247 (CONCHALI) | 3931.614773 (QUILICURA) |
| `ipp_pesos_hab` | 27701.980354 (CERRO NAVIA) | 1048997.007636 (LO BARNECHEA) |

**Métricas derivadas recalculadas de forma independiente:**

- `areas_verdes_m2 / poblacion` vs `areas_verdes_m2_hab`: diferencia absoluta máxima 4.7e-07.
- `ipp_miles_pesos * 1000 / poblacion` vs `ipp_pesos_hab`: diferencia absoluta máxima 4.8e-07.

Las diferencias son compatibles con el redondeo a 6 decimales del CSV.

## 9. SQLite baseline

| Check | Observado |
|---|---|
| `PRAGMA quick_check` | `ok` |
| `PRAGMA integrity_check` | `ok` |
| `PRAGMA foreign_key_check` | sin filas |
| Tablas | `dim_comuna`, `fact_desigualdad_comunal`, `metadata_fuentes` (más 3 autoindex de PK) |
| `dim_comuna` | 32 filas; PK `codigo_comuna TEXT`; 0 duplicados; 0 nulls |
| `fact_desigualdad_comunal` | 32 filas; PK `codigo_comuna TEXT` + `FOREIGN KEY → dim_comuna`; 0 duplicados; 0 nulls |
| `metadata_fuentes` | 4 filas; PK `id_fuente`; ids A, B, C, D; `anio_referencia` 2024/2024/2022/2024 |
| fact sin dim / dim sin fact | 0 / 0 |
| `nombre_comuna` en la fact | **no** (vive solo en `dim_comuna`), consistente con el modelo dimensión/hecho |

**Schemas:**

- `dim_comuna(codigo_comuna TEXT PK, nombre_comuna TEXT NN, provincia TEXT NN, region TEXT NN, fuente_referencia TEXT NN)`
- `fact_desigualdad_comunal(codigo_comuna TEXT PK FK, poblacion INTEGER, anio_poblacion INTEGER, pobreza_ingresos_pct REAL, anio_pobreza INTEGER, areas_verdes_m2 INTEGER, anio_areas_verdes INTEGER, ipp_miles_pesos INTEGER, anio_ingresos INTEGER, areas_verdes_m2_hab REAL, ipp_pesos_hab REAL)`
- `metadata_fuentes(id_fuente TEXT PK, nombre_fuente, institucion, url, fecha_descarga, formato, variable_principal, archivo_origen, archivo_logico, hoja TEXT NN; anio_referencia INTEGER; skiprows INTEGER; observaciones TEXT)`

## 10. CSV ↔ SQLite equivalence

Reconstrucción: `SELECT d.codigo_comuna, d.nombre_comuna, f.* FROM fact_desigualdad_comunal f JOIN dim_comuna d USING(codigo_comuna)`. La comparación contra el CSV se hizo con un outer merge por `codigo_comuna`. La tolerancia declarada fue `rtol=atol=1e-9`, pero no hizo falta: las columnas son **exactamente iguales**.

| Aspecto | Resultado |
|---|---|
| Filas | 32 vs 32 |
| Conjunto de llaves | idéntico; outer merge `both=32, left_only=0, right_only=0` |
| Columnas reconstruidas | mismas 12, mismo orden |
| `nombre_comuna` | igual en 32/32 |
| 10 columnas numéricas | `max_abs_diff = 0.0` y `exact=True` en todas |

## 11. Generated outputs

Todos los outputs esperados de F1–F9 existen, se regeneraron y sus contenidos son coherentes con el dataset y con SQLite:

| Output | Existe | Estado tras la ejecución |
|---|---|---|
| `outputs/perfilado_fuentes.xlsx` | sí | hash igual (ver nota de skip-write) |
| `outputs/conflictos_fuentes.md` | sí | hash igual |
| `outputs/homologacion_comunas.csv` | sí | hash igual |
| `outputs/resumen_homologacion.md` | sí | hash igual |
| `outputs/resumen_transformaciones.md` | sí | hash igual |
| `outputs/validacion_staging.csv` | sí | hash igual |
| `outputs/log_integracion.md` | sí | hash igual |
| `outputs/resumen_dataset_final.md` | sí | hash igual |
| `outputs/reporte_validacion_final.csv` / `.md` | sí | hash igual |
| `outputs/reporte_carga_sqlite.md` | sí | hash igual |
| `outputs/reporte_consultas_sqlite.csv` | sí | hash igual |
| `outputs/analisis_exploratorio.md` | sí | hash igual |
| `outputs/tablas_hallazgos_fase9.csv` | sí | hash igual |
| `outputs/ranking_{areas_verdes,pobreza,ipp}.csv` | sí | hash igual |
| `outputs/indice_rezago_territorial.csv` | sí | hash igual |
| `outputs/figures/` (5 PNG) | sí | **hash distinto** (ver abajo) |

**Anomalías u observaciones:**

1. **Figuras PNG.** Las 5 cambiaron de bytes; las dimensiones se mantienen (1350×900; el scatter 1275×975). La diferencia de píxeles es de 3–4 % con umbral 0.05 y la diferencia absoluta media está entre 0.013 y 0.019. La inspección visual de `pobreza_ingresos_top10.png` antes y después muestra las mismas comunas, el mismo orden, los mismos valores y los mismos títulos; solo cambian el renderizado de glifos y un desplazamiento de layout de pocos píxeles. Causa probable: matplotlib 3.11.2 con fuentes distintas a las del entorno original. No es un cambio semántico. Además, en la regeneración aislada desde cero las PNG salieron byte-idénticas a las del working tree, así que la salida es determinista dentro del entorno actual.
2. **Skip-write.** `load.py:267` (`_sqlite_has_expected_content`) y `extract.py:602` (`_workbook_matches_dataframes`) evitan reescribir SQLite y XLSX si el contenido ya coincide. Por eso un hash igual en el repo no prueba por sí solo que la regeneración sea byte-idéntica. Para cubrir eso se ejecutó una **regeneración desde cero** en una copia aislada (§12).
3. **Archivos en `outputs/` que no genera el pipeline.** `outputs/evaluacion_corta_fase9.md` y `outputs/reporte_correcciones_pre_fase10.md` están versionados en `outputs/`, pero ningún módulo de `src/` los escribe; solo los lee `tools/fase10/preparar_materiales.py`. Son artefactos históricos o manuales mezclados con outputs regenerables.

## 12. Artifact hashes

Se calculó SHA-256 de todos los archivos bajo `data/`, `db/` y `outputs/` (sin `.gitkeep`) antes y después de la ejecución. Los críticos:

| Artefacto | hash_before | hash_after | same/different |
|---|---|---|---|
| `data/processed/desigualdad_comunal_final.csv` | `66f481a82cf74d108507c9feaf83bc280ab3420e90d2dae7dbb74817897d98a4` | `66f481a82cf74d108507c9feaf83bc280ab3420e90d2dae7dbb74817897d98a4` | same |
| `db/lab1_desigualdad.sqlite` | `484e3d1bcab779f68aefd66cf76e95f50ebad8833b4e5631f88f76bd8cc70c62` | `484e3d1bcab779f68aefd66cf76e95f50ebad8833b4e5631f88f76bd8cc70c62` | same |
| `outputs/reporte_validacion_final.md` | `eeeab9cdc85b86418c394a75c8db754f46c9ffad122fea55ec527796bdb6b496` | `eeeab9cdc85b86418c394a75c8db754f46c9ffad122fea55ec527796bdb6b496` | same |
| `outputs/reporte_carga_sqlite.md` | `0f1e1e617712c6e7477dbb9f73fe66160931500f4218f2281f83029c6874aca1` | `0f1e1e617712c6e7477dbb9f73fe66160931500f4218f2281f83029c6874aca1` | same |
| `outputs/analisis_exploratorio.md` | `fbf3f2bbf886259d387e641797259e6532cd380a0c9a5c4d93b37f563ecd9528` | `fbf3f2bbf886259d387e641797259e6532cd380a0c9a5c4d93b37f563ecd9528` | same |
| `outputs/perfilado_fuentes.xlsx` | `3532b59835dfbfc47d4bb1476d07b1df698ba5d3ffb88f3ae39a18ac48404790` | `3532b59835dfbfc47d4bb1476d07b1df698ba5d3ffb88f3ae39a18ac48404790` | same |
| `outputs/figures/areas_verdes_m2_hab_bottom10.png` | `213aff17415a033b70d71c8e70d4428e26c8c080c7ea92dbdf4368cfdab1fa99` | `91af5ca11fe9285a6852eee7b6c891d65117647d2e62e7702ec5ce92077233d7` | different |
| `outputs/figures/indice_rezago_territorial_top10.png` | `931b2e7cdd3c1751dc9792ca493884fca129fc024b067d912dc643b0b93510c2` | `6c74a9c1ae391ec9add3c241877dc718c1097192e5e7aad365d79f5bffbd5ed1` | different |
| `outputs/figures/ipp_pesos_hab_bottom10.png` | `92728bff50c83c723cdfb9a120ce291a29b057bc06061e6f4cc22c3c1310234e` | `03e9954300c6b2e202ef9421f8d181bcfee8e30eff2d2f73e9d7c7c1f0e7df6e` | different |
| `outputs/figures/pobreza_ingresos_top10.png` | `a04871cd445ef8c8d35dac863ec69319c64e6a001749e03e735505dbe93eaf87` | `adad8df11e3ab8ec1873fc80e4bb28f2d4654eb8f8b2189b1714436868481b6a` | different |
| `outputs/figures/pobreza_vs_areas_verdes_scatter.png` | `1c9416e110ad628ed6afd2f1ddb380ff60c61bc9cdc3d00b062147a026ff0853` | `218b57020e92e1c8badea06fde13f8ff2d522630d2fd56bebddbebb6263ec44c` | different |

Todos los archivos restantes bajo `data/` (incluidos los raw y el staging) y `outputs/` tienen hash igual antes y después.

**Rerun inmediato (idempotencia):** un segundo `python -m src.main` terminó con exit 0 y stdout idéntico. Ningún archivo cambió de hash respecto de la primera ejecución.

**Regeneración desde cero (verificación adicional, fuera del repo):**

- Procedimiento: `git archive HEAD` extraído en el scratchpad. Se borraron staging, dataset final, SQLite y todos los outputs que genera el pipeline, y luego se ejecutó `python -m src.main`.
- Resultado: exit 0, stderr vacío, stdout idéntico salvo la línea 1, que incluye el nombre del directorio (`PROJECT_NAME` se deriva de `BASE_DIR.name`).
- Staging, CSV final, todos los `.md`/`.csv` de outputs y las 5 PNG: **byte-idénticos** al working tree.
- `db/lab1_desigualdad.sqlite`: bytes distintos (5083 bytes, en la cabecera y el layout de páginas), pero `iterdump()` es **idéntico** (73 sentencias).
- `outputs/perfilado_fuentes.xlsx`: bytes distintos, pero los valores de celda de ambas hojas (`resumen` 5 filas, `columnas` 28 filas) son **idénticos**. Solo difieren los metadatos `created`/`modified` del workbook.

## 13. Quilicura outlier status

| Rank | Código | Comuna | `areas_verdes_m2` | `poblacion` | `areas_verdes_m2_hab` |
|---|---|---|---|---|---|
| 1 | 13125 | QUILICURA | 808434356 | 205624 | **3931.614773** |
| 2 | 13113 | LA REINA | 1953250 | 89870 | 21.734172 |
| 3 | 13123 | PROVIDENCIA | 2904368 | 143974 | 20.172865 |
| 4 | 13122 | PEÑALOLEN | 3077091 | 236478 | 13.012166 |
| 5 | 13119 | MAIPU | 4018982 | 503635 | 7.979950 |

- El valor de Quilicura es ~180.9 veces el segundo mayor; la mediana de las 32 comunas es 4.597607.
- Tratamiento actual en el repositorio:
  - `src/analyze.py:575` lo declara "outlier plausible" que "debe interpretarse como caso especial".
  - `src/analyze.py:433-453` etiqueta QUILICURA en el scatter y agrega una nota.
  - `analyze.py:626` y `outputs/analisis_exploratorio.md:88` indican que el scatter usa escala logarítmica en X.
  - `outputs/evaluacion_corta_fase9.md:15` lo describe como "outlier extremo".
- El valor se mantiene en el CSV y en SQLite. No se encontró código que lo recorte, capee o reemplace.
- P00 no modificó este valor.

## 14. Phase 10 discrepancy

**Hechos observados:**

1. El texto actual de `README.md` ("Las Fases 10, 11 y 12 no forman parte del trabajo tecnico cerrado de este repositorio aun. `docs/informe/` y `docs/presentacion/` se mantienen reservados para esas etapas.") se introdujo en `050aeed` (2026-04-03, "chore: alinear README y estabilizar ejecución e idempotencia pre-Fase 10"). `git log -S` no encuentra otro commit que toque esa frase.
2. `10d3bec` (2026-04-03, "feat: finaliza fase 10 e implementa código para generar informe final") agregó 47 archivos y +2695 líneas:
   - `docs/informe_lab1_materiales/`: fragmentos LaTeX de `Resumen.tex`, `Secciones/01–14`, `Anexos/`, `Tablas/*.tex`, copias de las 5 figuras, `referencias_lab1.bib`, `trazabilidad_informe.csv`, `reporte_preparacion_fase10.md`, y un sandbox `_validacion/` con `main_sandbox.tex`/`.pdf` compilado con `pdflatex`;
   - `tools/fase10/preparar_materiales.py` (1705 líneas), que lee los productos del pipeline (CSV, SQLite, outputs) y genera esos materiales.
   - Este commit **no modificó `README.md`**.
3. `bbff850` ("Update README.md") solo eliminó las 3 primeras líneas del README (título `lab1-bi-1s2026` y la descripción del curso). No tocó la frase sobre Fases 10–12.
4. Todos esos archivos **siguen presentes en `main`** (HEAD `e5a4dbf`).
5. `src/` no referencia `tools/fase10` ni `docs/informe_lab1_materiales`, y `src/main.py` solo recorre las Fases 1–9 (`config.PROJECT_PHASE = "Fase 9"`). `docs/informe/` y `docs/presentacion/` siguen vacíos (solo `.gitkeep`).
6. Las 5 figuras en `docs/informe_lab1_materiales/Figuras/` son byte-idénticas a las de `outputs/figures/` en HEAD. Tras esta ejecución, esas copias ya no coinciden con las PNG regeneradas; la diferencia es solo de renderizado (§11).

**Naturaleza de la discrepancia (inferencia a partir de la evidencia):**

- En este repositorio, "Fase 10" corresponde a **preparación de materiales académicos o editoriales** para un informe LaTeX: un generador en `tools/` y fragmentos en `docs/informe_lab1_materiales/`. No es una extensión del pipeline ETL.
- El README se redactó antes de ese commit y no se actualizó después. Por eso su afirmación "Fase 10 no forma parte del trabajo técnico cerrado" es literalmente coherente con el pipeline técnico, pero no menciona que los materiales de Fase 10 existen, ni que viven en `docs/informe_lab1_materiales/` y no en `docs/informe/`.
- El mensaje de commit "finaliza fase 10" se refiere a esos materiales. No hay evidencia en el repo de que el informe final se haya integrado a un template externo: `reporte_preparacion_fase10.md` lista esa integración como pendiente.

**Conclusión:** no se declara Fase 10 "cerrada" ni "inexistente". Existe como paquete de materiales de informe, separado del pipeline, y el README no lo refleja. No se modificó nada; la corrección requiere su propio scope.

## 15. Validation matrix

| Check | Estado | Esperado | Observado | Evidencia |
|---|---|---|---|---|
| Working tree inicial seguro | PASS | limpio | limpio en `main` @ `e5a4dbf` | `git status --short` |
| Pipeline local ejecuta | PASS | exit 0 | exit 0, stderr vacío | `python -m src.main` |
| Rerun idempotente | PASS | sin cambios adicionales | 0 hashes distintos entre run 1 y run 2 | sha256 run1 vs run2 |
| Regeneración desde cero | PASS | semánticamente idéntica | CSV/MD/PNG byte-idénticos; SQLite `iterdump` y XLSX con celdas idénticas | copia `git archive` aislada |
| Fuentes A–D presentes | PASS | 4 | 4 | filesystem + preflight |
| SINIM como SpreadsheetML | PASS | parser XML | `spreadsheetml_xml_2003` en A y B | `extract.py:334`, stdout, `file` |
| Dim maestra | PASS | 32, llave única, provincia y región únicas | 32; 0 nulls; 0 dup código; 0 dup nombre; SANTIAGO; METROPOLITANA DE SANTIAGO | pandas sobre CSV |
| Dataset filas | PASS | 32 | 32 | CSV |
| Dataset columnas | PASS | 12, en orden | 12, orden exacto | CSV |
| Key nulls | PASS | 0 | 0 | CSV |
| Key duplicados | PASS | 0 | 0 | CSV |
| Cobertura faltante | PASS | 0 | `[]` | comparación dim |
| Cobertura extra | PASS | 0 | `[]` | comparación dim |
| Nulls en columnas finales | PASS | 0 | 0 en las 12 | CSV |
| Año población | PASS | 2024 | `[2024]` | CSV |
| Año pobreza | PASS | 2022 | `[2022]` | CSV |
| Año áreas verdes | PASS | 2024 | `[2024]` | CSV |
| Año ingresos | PASS | 2024 | `[2024]` | CSV |
| Métricas derivadas recalculadas | PASS | coherentes | máx. diferencia ≤ 4.8e-07 (redondeo a 6 decimales) | recálculo pandas |
| SQLite quick_check | PASS | ok | ok (`integrity_check` también ok) | SQLite |
| SQLite foreign_key_check | PASS | sin violaciones | sin filas | SQLite |
| `dim_comuna` | PASS | 32 | 32 | SQLite |
| `fact_desigualdad_comunal` | PASS | 32 | 32 | SQLite |
| `metadata_fuentes` | PASS | 4 | 4 | SQLite |
| Duplicados de llave en SQLite | PASS | 0 | 0 en dim y en fact | SQLite |
| Cobertura dim/fact | PASS | 0/0 | 0/0 | SQLite |
| CSV ↔ SQLite keys | PASS | equivalentes | 32/32, outer merge sin huérfanas | comparación |
| CSV ↔ SQLite métricas | PASS | equivalentes | `max_abs_diff = 0.0` en las 10 numéricas; nombres iguales | comparación |
| Outputs F1–F9 | PASS | presentes | todos presentes | filesystem |
| Hash CSV / SQLite | PASS | estable | same / same | sha256 |
| Hash figuras | PASS | sin cambio semántico | bytes distintos; mismo contenido visual y dimensiones | pixel diff + inspección visual |
| Quilicura preservado | PASS | valor intacto | 3931.614773, sin tratamiento | CSV, SQLite |
| AGENTS = CLAUDE | PASS | idénticos | `cmp` exit 0 | `cmp` |
| Tests automatizados | NO EJECUTADA | — | no existe suite ni framework | filesystem |
| CI | NO EJECUTADA | — | no existe `.github/workflows/` | filesystem |
| Discrepancia Fase 10 investigada | PASS | hechos documentados | ver §14 | git log/show |

## 16. Git state after execution

```text
$ git branch --show-current
chore/p00-baseline-local-audit

$ git status --short
 M outputs/figures/areas_verdes_m2_hab_bottom10.png
 M outputs/figures/indice_rezago_territorial_top10.png
 M outputs/figures/ipp_pesos_hab_bottom10.png
 M outputs/figures/pobreza_ingresos_top10.png
 M outputs/figures/pobreza_vs_areas_verdes_scatter.png
?? docs/ai/

$ git diff --stat
 outputs/figures/areas_verdes_m2_hab_bottom10.png    | Bin 54451 -> 51681 bytes
 outputs/figures/indice_rezago_territorial_top10.png | Bin 59451 -> 55730 bytes
 outputs/figures/ipp_pesos_hab_bottom10.png          | Bin 55108 -> 49410 bytes
 outputs/figures/pobreza_ingresos_top10.png          | Bin 54928 -> 52474 bytes
 outputs/figures/pobreza_vs_areas_verdes_scatter.png | Bin 67321 -> 64457 bytes
```

| Cambio | Origen |
|---|---|
| 5 PNG en `outputs/figures/` | regeneración legítima del pipeline (renderizado del entorno actual) |
| `docs/ai/reports/R00_baseline_local_audit.md` (untracked) | creación de R00 |
| Cambios preexistentes | ninguno |
| Diferencias inesperadas | ninguna semántica |

No se revirtió nada. HEAD sigue en `e5a4dbf`, sin commits, push, merge ni PR.

## 17. Deviations from P00

1. **Entorno de ejecución.** El `python` del sistema no tiene pip ni pandas, openpyxl o matplotlib. No se podía ejecutar `python -m pip install -r requirements.txt` sobre el intérprete del sistema sin modificar el sistema (p. ej. con `--break-system-packages` o `dnf`). Se creó un venv **fuera del repositorio** (scratchpad de sesión) con el mismo Python 3.14.7, se ejecutó ahí exactamente `python -m pip install -r requirements.txt` y luego `python -m src.main` con ese intérprete. No se modificó `requirements.txt` ni se agregaron dependencias, y no se escribió nada en el repo.
2. **`MPLBACKEND=Agg`** en el entorno de ejecución. Es redundante porque `src/analyze.py:12` ya fija el backend Agg, así que no altera el comportamiento.
3. **Verificaciones adicionales no pedidas explícitamente**, todas de solo lectura o sobre copias fuera del repo: `integrity_check` y `foreign_key_check`, recálculo de métricas derivadas, rerun de idempotencia, regeneración desde cero en una copia `git archive` y comparación de píxeles de las PNG.
4. El prompt P00 **no se guardó** en `docs/ai/prompts/` porque queda fuera del write scope de P00.

## 18. Issues and unresolved questions

Ninguno bloquea P01. Todos requieren un scope propio y ninguno se corrigió aquí.

1. **Dependencias sin versión fija.** `requirements.txt` no fija versiones. Hoy resuelve a pandas 3.0.6 y matplotlib 3.11.2, y eso ya cambia los bytes de las figuras. Los productos de datos fueron idénticos, pero la reproducibilidad a futuro no está garantizada. Candidato a un scope de lockfile o pinning.
2. **Figuras PNG modificadas en el working tree.** Hay que decidir si se conservan las PNG regeneradas o se restauran las de HEAD (`git restore outputs/figures/`). P00 no las revirtió. Consecuencia: las copias en `docs/informe_lab1_materiales/Figuras/` ya no coinciden byte a byte con `outputs/figures/`.
3. **Entorno local sin pip ni dependencias.** Ejecutar el baseline requiere un venv. No está documentado en el README.
4. **Outputs no regenerables dentro de `outputs/`.** `evaluacion_corta_fase9.md` y `reporte_correcciones_pre_fase10.md` no los genera el pipeline.
5. **README desactualizado en varios puntos:**
   - no refleja los materiales de Fase 10 (`docs/informe_lab1_materiales/`, `tools/fase10/`);
   - el árbol de "Estructura principal" usa la raíz `lab1-bi-1s2026/` y omite `tools/`, `docs/informe_lab1_materiales/`, `AGENTS.md` y `CLAUDE.md`;
   - no menciona `docs/ai/`.
6. **Hash de SQLite y XLSX no es un criterio de reproducibilidad por sí solo.** Por la lógica de skip-write y por los metadatos de SQLite y del workbook, una regeneración desde cero produce bytes distintos con contenido idéntico. Para comparar con Lakehouse conviene usar comparación semántica (iterdump o consultas), no el hash.
7. **Sin tests ni CI.** Toda la protección de regresión está embebida en el pipeline. Registrado como estado del baseline, no como defecto.
8. **`PROJECT_NAME` depende del nombre del directorio** (`config.py`, `BASE_DIR.name`). Solo afecta la línea 1 de stdout; no se observó impacto en los artefactos.
9. **Salida de `main()` ante dataset no apto.** `main()` imprime "no apto" tras Fase 7 pero no retorna ≠0 en ese punto; la detención depende de los `raise` posteriores (p. ej. `analyze.py:667`). No se ejercitó el camino de fallo, solo se observó en el código.

## 19. Gate recommendation

**APPROVE P01**

El baseline local es:

- ejecutable (exit 0);
- medido (CSV, SQLite y outputs verificados de forma directa);
- equivalente CSV ↔ SQLite de forma exacta;
- idempotente en rerun;
- reproducible desde cero a nivel semántico.

Los issues de la §18 no invalidan su uso como referencia funcional para la implementación Lakehouse. Antes de congelar el baseline como referencia de comparación conviene resolver el issue 1 (pinning) y el issue 2 (decisión sobre las PNG).

## 20. Evidence locations

| Evidencia | Ubicación |
|---|---|
| Código inspeccionado | `src/*.py`, `tools/fase10/preparar_materiales.py`, `requirements.txt`, `.gitignore`, `README.md` |
| Insumos | `data/raw/metadata_fuentes.csv`, `data/raw/dim_comuna_base.csv`, `data/raw/*.xls{,x}` |
| Dataset final | `data/processed/desigualdad_comunal_final.csv` (sha256 `66f481a82cf74d108507c9feaf83bc280ab3420e90d2dae7dbb74817897d98a4`) |
| SQLite | `db/lab1_desigualdad.sqlite` (sha256 `484e3d1bcab779f68aefd66cf76e95f50ebad8833b4e5631f88f76bd8cc70c62`) |
| Reportes del pipeline | `outputs/*.md`, `outputs/*.csv`, `outputs/perfilado_fuentes.xlsx`, `outputs/figures/*.png` |
| Diff de Git | `git status --short`, `git diff --stat` en la branch `chore/p00-baseline-local-audit` |
| Historial de Fase 10 | `git show --stat 050aeed 10d3bec bbff850`; `git log -S "Fases 10, 11 y 12" -- README.md` |
| Evidencia efímera de sesión (fuera del repo, no persistente) | scratchpad de la sesión Claude Code: `run_stdout.txt`, `run_stderr.txt`, `rerun_stdout.txt`, `clean_stdout.txt`, `hash_before.txt`, `hash_after.txt`, `hash_rerun.txt`, `validate.py`, `validate_out.txt`, `pip_install.log`, copia `clean/` y `png_before/` |

Nota: la evidencia de scratchpad no persiste. Las cifras relevantes quedan transcritas en este reporte y se pueden reproducir con el procedimiento descrito: venv con `requirements.txt` + `python -m src.main` + las consultas de las §8–§10.
