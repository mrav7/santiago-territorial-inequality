# E04-E — Silver Rerun Runtime Evidence

## 1. Identificación

| Campo | Valor |
|---|---|
| Fecha | Rerun: timestamp Delta de la versión 1 = `2026-09-26 00:12:57`, tal como lo mostró `DESCRIBE HISTORY` (zona horaria no registrada en la evidencia). Documento persistido el 2026-09-25 (hora local -03:00). |
| Etapa | `C04-E — Stabilize Silver Rerun Contract` |
| Notebook | `databricks/notebooks/02_silver_poverty.py` (versión C04-E, no commiteada a la fecha de la ejecución; base `1425763`) |
| SQL validator | `databricks/sql/02_validate_silver_poverty.sql` |
| Entorno | Databricks Free Edition; notebook en compute serverless; SQL en SQL Warehouse. Workspace no identificado en este documento. |
| Tipo de evidencia | Ejecución **manual humana** en Databricks, revisada por el responsable del proyecto. Los resultados se transcriben aquí. El agente local no ejecutó nada en Databricks. |

No se registran run IDs, URLs ni capturas porque no fueron suministrados.

## 2. Propósito

**Qué se quiso demostrar:** que `workspace.silver.pobreza_ingresos` puede regenerarse ejecutando el mismo notebook sobre un target Silver **ya existente**, sin editar flags ni código. Además, que el target existente se valida (TC-S01…S04) antes de sobrescribirlo, que se mantienen DQ y equivalencia, que Delta registra una nueva versión y que no hay acumulación de filas.

**Qué NO se afirma:**
- `MERGE`;
- carga incremental;
- idempotencia incremental;
- schema evolution;
- rerun de Bronze dentro de esta ejecución.

La capability es un **snapshot overwrite batch**.

## 3. Estado PRE-rerun

Consultas manuales: `SELECT COUNT(*) FROM workspace.silver.pobreza_ingresos` y `DESCRIBE HISTORY workspace.silver.pobreza_ingresos`.

| Campo | Valor observado |
|---|---|
| Row count | 32 |
| Delta version (última) | 0 |
| Operation | `CREATE OR REPLACE TABLE AS SELECT` |
| numOutputRows | 32 |
| Timestamp | `2026-09-24 14:28:39` |

El número absoluto de versión es evidencia histórica de esta ejecución, no un contrato futuro.

## 4. Notebook rerun

`02_silver_poverty.py` ejecutado completo (`Run all`) con el target Silver existente y sin modificar código ni flags.

Resumen impreso por el notebook:

```text
Bronze rows                        351
valid commune rows                 345 (4 digits=206, 5 digits=139)
non-commune rows                   6 (NULL=1, other=5)
valid commune codes outside master 313
master commune rows                32
master keys missing from source    0
Silver candidate rows              32
Silver Delta rows                  32
equivalence tolerance / max diff   1e-09 / 0E-10
target existed before this run     True
Delta version before / after       0 / 1
```

## 5. Data Quality

Todos en `PASS` (IDs sin renumerar; DQ-S18 se ejecuta antes que DQ-S13):

```text
PASS  DQ-S01  Bronze table exists and is Delta
PASS  DQ-S02  Bronze row count
PASS  DQ-S03  Bronze required contract of the current snapshot (columns, metadata, single snapshot, decimal poverty)
PASS  DQ-S04  master dimension file size + SHA-256 = repository
PASS  DQ-S05  validation fixtures size + SHA-256 = repository (staging + processed)
PASS  DQ-S06  master dimension: 32 rows, 32 distinct non-null keys, names present
PASS  DQ-S07  valid commune-code rows in Bronze
PASS  DQ-S08  non-commune rows removed
PASS  DQ-S09  distinct valid commune codes (no duplicate codes)
PASS  DQ-S10  valid codes cast to codigo_comuna without nulls
PASS  DQ-S11  intersection with master dimension
PASS  DQ-S12  master keys missing from source
PASS  DQ-S18  poverty proportion valid before transform (0 nulls, 0–1)
PASS  DQ-S13  Silver row count
PASS  DQ-S14  codigo_comuna non-null
PASS  DQ-S15  codigo_comuna unique
PASS  DQ-S16  Silver key coverage = master (0 missing, 0 extra)
PASS  DQ-S17  nombre_comuna non-null
PASS  DQ-S19  pobreza_ingresos_pct non-null
PASS  DQ-S20  pobreza_ingresos_pct within 0–100
PASS  DQ-S21  anio_pobreza only 2022
PASS  DQ-S22  Silver schema = contract
PASS  DQ-S23  Silver table exists after write
PASS  DQ-S24  DESCRIBE DETAIL format = delta
PASS  DQ-S25  Delta post-write row count
PASS  DQ-S26  persisted rows equal the validated Silver rows
```

## 6. Baseline Equivalence

Todos en `PASS`:

```text
PASS  EQ-S01  baseline row count
PASS  EQ-S02  baseline keys: 32 distinct, 0 null, 0 duplicate
PASS  EQ-S03  Silver key set = baseline key set (both directions)
PASS  EQ-S04  canonical nombre_comuna equal by key
PASS  EQ-S05  anio_pobreza exact by codigo_comuna vs desigualdad_comunal_final.csv
PASS  EQ-S06  pobreza_ingresos_pct abs diff <= tolerance
PASS  EQ-S07  null profile equivalent (0 nulls in compared columns, both sides)
PASS  EQ-S08  duplicate profile: 0 duplicate keys in Silver and baseline
PASS  EQ-S09  semantic types equivalent (every fixture value casts cleanly to the Silver semantic type)
PASS  EQ-S10  joined comparison coverage: 32 matched / 0 unmatched
```

| Campo | Valor |
|---|---|
| Tolerance | `1e-09` |
| max_abs_diff | `0E-10` (= 0) |

## 7. Target Compatibility

Todos en `PASS`:

```text
PASS  TC-S01  existing target is Delta                                          (pre-write)
PASS  TC-S02  existing target schema = Silver contract                          (pre-write)
PASS  TC-S03  existing target keys: 32 rows, 32 distinct non-null keys = master (pre-write)
PASS  TC-S04  existing target rows equal the validated candidate                (pre-write)
PASS  TC-S05  rerun created a new Delta version                                 (post-write)
```

El target preexistente se trató como caso normal y se validó antes del overwrite.

## 8. Post-write state

| Campo | Valor observado |
|---|---|
| Schema | `codigo_comuna int`, `nombre_comuna string`, `pobreza_ingresos_pct decimal(7,4)`, `anio_pobreza int` |
| Rows | 32 (antes: 32) |
| Keys | 32 distintas; cobertura exacta de la dimensión maestra (DQ-S16) |
| Nulls | 0 en las cuatro columnas (DQ-S14, S17, S19; SQL §9) |
| Duplicates | 0 |
| Year | `anio_pobreza` = 2022 en las 32 filas |
| Range | 0.8910 – 9.2938, 0 fuera de rango (SQL §9) |
| Persistido vs candidate | diferencia 0 (DQ-S26) |
| Versions | before / after = 0 / 1 |

`DESCRIBE HISTORY` observado:

| version | timestamp | operation | numOutputRows |
|---|---|---|---|
| 0 | 2026-09-24 14:28:39 | CREATE OR REPLACE TABLE AS SELECT | 32 |
| 1 | 2026-09-26 00:12:57 | CREATE OR REPLACE TABLE AS SELECT | 32 |

Resultado: `version_after > version_before`, 32 → 32 filas, sin acumulación.

## 9. Independent SQL Validation

`02_validate_silver_poverty.sql` ejecutado completo (`Run all`) en SQL Warehouse. Databricks mostró **12 result sets**.

| Bloque | Valores observados |
|---|---|
| Existencia (`SHOW TABLES`) | database = `silver`, tableName = `pobreza_ingresos`, isTemporary = false |
| Schema | `codigo_comuna int`, `nombre_comuna string`, `pobreza_ingresos_pct decimal(7,4)`, `anio_pobreza int` |
| Formato físico (`DESCRIBE DETAIL`) | format = `delta`, name = `workspace.silver.pobreza_ingresos` |
| Row count / keys | row_count = 32, distinct_commune_keys = 32, duplicate_rows = 0 |
| Detalle de duplicados | No rows returned |
| Nulls | null_codigo_comuna = 0, null_nombre_comuna = 0, null_pobreza = 0, null_anio = 0 |
| Rango de pobreza | min = 0.8910, max = 9.2938, out_of_range = 0 |
| Año | anio_pobreza = 2022, n = 32 |
| Cobertura maestra | matched_keys = 32, master_keys_missing_in_silver = 0, silver_keys_outside_master = 0 |
| Muestra | 32 filas |
| Delta history | versiones 0 y 1; la versión 1 corresponde al rerun, con 32 filas |

## 10. Runtime Gate

| Criterio | Estado | Evidencia |
|---|---|---|
| RT-01 target preexistente | PASS | `target existed before this run = True`; row count PRE = 32 |
| RT-02 target compatibility | PASS | TC-S01…TC-S04 PASS |
| RT-03 DQ-S01…S26 | PASS | todos los checks PASS (§5) |
| RT-04 EQ-S01…S10 | PASS | todos los checks PASS (§6) |
| RT-05 contrato Silver | PASS | 32 filas, 32 keys, 0 duplicados, 0 nulls, año 2022 (§8, §9) |
| RT-06 equivalencia | PASS | tolerance `1e-09`, max diff `0E-10` |
| RT-07 nueva versión Delta | PASS | versión `0 → 1`; TC-S05 PASS |
| RT-08 sin acumulación | PASS | 32 → 32 |
| RT-09 persistido = candidate | PASS | DQ-S26 PASS (diferencia 0) |
| RT-10 SQL independiente | PASS | ejecución completa, 12 result sets coherentes (§9) |

## 11. Limitaciones

- Evidencia obtenida y transcrita manualmente. No hay run ID ni capturas versionadas.
- No es `MERGE`, no es carga incremental, no es idempotencia incremental y no es schema evolution. Esas capabilities corresponden a P09 y P10.
- TC-S04 exige igualdad entre target y candidate. Es válido porque la fuente y los fixtures están fijados por hash. Un cambio legítimo de fuente bloquearía el rerun hasta revisar el contrato.
- TC-S05 es evidencia post-write, no una protección pre-write.
- La evidencia suministrada no incluye un rerun Bronze ni el historial Bronze observado. El desacople del historial Bronze (DQ-S03 sin lock `[0, 1]`) está verificado estáticamente en R04-E. En runtime solo consta que DQ-S03 pasó con el historial Bronze vigente en ese momento.
- El número absoluto de versión (0 → 1) es propio de esta ejecución, no un contrato.

## 12. Conclusión

**C04-E = GATE_PASSED**

Capability demostrada: **rerun batch snapshot overwrite seguro y validado para Silver pobreza**.
