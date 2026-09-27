# Evidencia runtime — dimensión maestra comunal Silver

## Alcance y procedencia

Este documento registra los resultados de la ejecución humana en Databricks del [notebook de la dimensión comunal](../../../databricks/notebooks/03_silver_commune_dimension.py) y de su [validador SQL](../../../databricks/sql/03_validate_silver_commune_dimension.sql). La fuente fue `/Volumes/workspace/bronze/source_files/dim_comuna_base.csv`, copia del archivo versionado `data/raw/dim_comuna_base.csv`; el destino fue `workspace.silver.dim_comuna`. Los valores siguientes fueron suministrados por el responsable del proyecto. El agente que redactó este documento no ejecutó Databricks. No se suministró la fecha exacta de ejecución.

## Contrato

| Columna | Tipo Silver |
|---|---|
| `codigo_comuna` | `INT` |
| `nombre_comuna` | `STRING` |
| `provincia` | `STRING` |
| `region` | `STRING` |
| `fuente_referencia` | `STRING` |

El grano es una fila por comuna: 32 comunas de la Provincia de Santiago. `codigo_comuna` es la llave canónica, sin surrogate key. El notebook lee inicialmente las cinco columnas como `STRING`, en el mismo orden, y convierte la llave a `INT` después de validarla.

## Identidad y calidad de la fuente

El archivo del Volume registró **1779 bytes** y SHA-256 `c8e831949b07bbefed64ffd0e50ee73937c657bbb5071b3741007b9e73532aad`. El encabezado observado fue `codigo_comuna,nombre_comuna,provincia,region,fuente_referencia`. Los checks de identidad y lectura reportaron `PASS`.

| Perfil de la fuente | Valor observado |
|---|---:|
| Filas | 32 |
| Llaves nulas o blancas | 0 |
| Llaves no convertibles a `INT` | 0 |
| Llaves distintas | 32 |
| Llaves duplicadas | 0 |
| Nombres nulos o blancos | 0 |
| Nombres distintos | 32 |
| Referencias nulas o blancas | 0 |

Las 32 filas tienen `provincia = SANTIAGO` y `region = METROPOLITANA DE SANTIAGO`. Los checks de calidad de fuente reportaron `PASS`.

## Candidate, equivalencia y tabla persistida

El candidate tuvo 32 filas, 32 `codigo_comuna` distintos y ninguna llave nula. Su schema coincidió con el contrato anterior. La comparación por llave contra el CSV, después del cast controlado, produjo **32 matched, 0 source-only y 0 candidate-only**. Hubo cero diferencias por llave en `nombre_comuna`, `provincia`, `region` y `fuente_referencia`. Los checks correspondientes reportaron `PASS`.

En el rerun, el target ya existía. Antes del overwrite se observó `format = delta`, `table_type = MANAGED`, 32 filas, 32 llaves distintas, ninguna llave nula, cero llaves exclusivas en cada lado y cero filas diferentes entre target y candidate. Todos los checks de compatibilidad pre-write reportaron `PASS`.

Después del write, `workspace.silver.dim_comuna` siguió con `format = delta` y `table_type = MANAGED`: 32 filas, 32 llaves distintas, ninguna llave nula y cero filas diferentes frente al candidate. Los checks post-write reportaron `PASS`.

## Rerun batch y Delta History

| Versión | Operación observada | `isManaged` | Filas escritas | Archivos removidos | Bytes removidos | `readVersion` |
|---:|---|---|---:|---:|---:|---:|
| 0 | `CREATE OR REPLACE TABLE AS SELECT` | `true` | 32 | 0 | 0 | `null` |
| 1 | `CREATE OR REPLACE TABLE AS SELECT` | `true` | 32 | 1 | 2224 | 0 |

Delta History atribuyó ambas versiones al mismo notebook. El log completo de checks conservado corresponde al **rerun**: target preexistente, versión 0 antes y versión 1 después. El check `version_after > version_before` reportó `PASS`. El resumen fue 32 filas fuente → 32 candidate → 32 persistidas; el contenido lógico no cambió y no hubo acumulación. Esto demuestra un **rerun batch por snapshot overwrite compatible**, no una carga incremental.

## Validación SQL independiente

El validador SQL se ejecutó completo y produjo **15 result sets**. Confirmó la presencia de `dim_comuna` y `pobreza_ingresos` en `workspace.silver`; cinco columnas con los tipos del contrato; `format = delta`; `table_type = MANAGED`; 32 filas; 32 llaves distintas; cero llaves nulas; y ninguna fila devuelta por la consulta de duplicados.

El perfil de nulos y blancos dio cero en las cinco columnas, con 32 nombres distintos. La distribución territorial fue `SANTIAGO = 32` y `METROPOLITANA DE SANTIAGO = 32`; `fuente_referencia = A` en las 32 filas. La lectura SQL independiente del CSV encontró 32 filas, 32 llaves distintas, cero llaves blancas y cero no convertibles. La comparación SQL obtuvo **32 matched, 0 source-only, 0 silver-only y cero diferencias** en nombre, provincia, región y referencia. La inspección ordenada mostró las 32 comunas, de `13101` a `13132`.

## Límite de la evidencia

No se conservó el log completo de checks de la **ejecución inicial**. Su creación queda respaldada por Delta History versión 0: `isManaged = true`, 32 filas escritas, ningún archivo removido y `readVersion = null`. El estado persistido resultante se validó después mediante los checks completos del rerun y el SQL independiente. No se recreó ni eliminó la tabla para producir un nuevo log inicial. Por ello, este documento no declara que se conserve un `PASS` de cada check del run inicial.

## Resultado y alcance de la capacidad

La dimensión maestra Silver fue aprobada para servir como referencia comunal de los siguientes verticales Silver. La evidencia demuestra una tabla Delta managed, lectura con schema explícito, identidad de fuente, Data Quality, equivalencia exacta con el maestro, compatibilidad del target, rerun batch seguro y validación SQL independiente.

Este cierre no demuestra ni implementa `MERGE`, cargas incrementales, schema evolution, integración Gold, Jobs/Workflows, Power BI ni preparación para producción. Esas capacidades siguen fuera de este resultado.
