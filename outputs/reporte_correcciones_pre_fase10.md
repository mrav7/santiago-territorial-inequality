# Reporte de correcciones pre Fase 10

## 1. Resumen ejecutivo breve

Se corrigieron tres problemas reales detectados en el repositorio:

- `README.md` estaba desactualizado y describia el proyecto como si estuviera en Fase 5.
- `python -m src.main` fallaba por imports no compatibles con ejecucion como modulo.
- la reejecucion del pipeline reserializaba artefactos binarios innecesariamente.

Resultado final:

- `python src/main.py` funciona.
- `python -m src.main` funciona.
- el dataset final sigue consistente con 32 filas y 12 columnas.
- SQLite sigue valida con tablas `dim_comuna`, `fact_desigualdad_comunal` y `metadata_fuentes` en conteos 32 / 32 / 4.
- una corrida limpia seguida de un rerun inmediato no deja cambios espurios adicionales en Git.

Hallazgos no aplicados por no corresponder a bug:

- no se agrego `nombre_comuna` a `fact_desigualdad_comunal`; el modelo dimension-hecho ya era correcto.
- no se completaron `docs/informe/` ni `docs/presentacion/`; siguen reservados para Fases 10 y 11.

## 2. Linea base observada

Estado inicial observado:

- rama: `main...origin/main`
- `git status --short --branch`: sin cambios versionados al inicio

Comandos ejecutados para reproducir:

- `git status --short --branch`
- `find . -maxdepth 3 -type f | sort`
- `sed -n '1,240p' README.md`
- `rg -n "^(from|import) " src`
- `python -m compileall -q src`
- `python src/main.py`
- `python -m src.main`

Problemas reproducidos con evidencia:

1. README desactualizado

- `README.md` declaraba que el proyecto estaba en **Fase 5**.
- el mismo archivo afirmaba que "Todavia no se implementa el ETL completo. El proyecto no integra aun el dataset final ni genera SQLite."
- esa descripcion no coincidia con el repo real, que ya incluye `data/processed/desigualdad_comunal_final.csv`, `db/lab1_desigualdad.sqlite` y outputs de Fase 6 a 9.

2. Ejecucion como modulo fallida

- `python src/main.py`: ejecuto correctamente.
- `python -m src.main`: fallo con `ModuleNotFoundError: No module named 'config'`.

3. Rerun sucio antes de las correcciones

- sobre un arbol limpio, una corrida de `python src/main.py` dejo modificados:
  - `db/lab1_desigualdad.sqlite`
  - `outputs/perfilado_fuentes.xlsx`
- evidencia observada en `git diff --stat`:
  - `db/lab1_desigualdad.sqlite | Bin 28672 -> 28672 bytes`
  - `outputs/perfilado_fuentes.xlsx | Bin 8295 -> 8296 bytes`

## 3. Cambios aplicados

### `README.md`

- se actualizo para reflejar el estado real del repo: Fases 1 a 9 implementadas, dataset final, SQLite, artefactos analiticos y pasos de ejecucion reales.
- se incorporaron ambos modos soportados de ejecucion:
  - `python src/main.py`
  - `python -m src.main`
- se mantuvo enfoque tecnico y operativo, sin adelantar informe ni presentacion.

### `src/__init__.py`

- se agrego para formalizar `src` como paquete del proyecto.

### `src/main.py`

- se agrego bootstrap minimo de `sys.path` para soportar `python src/main.py` sin romper imports de paquete.
- se migraron imports internos a `from src...`.

### `src/analyze.py`
### `src/comunas.py`
### `src/integrate.py`
### `src/transform.py`
### `src/validate.py`

- se migraron imports internos a `from src...` para compatibilidad consistente con ejecucion como modulo.

### `src/extract.py`

- se mantuvo la generacion de `outputs/perfilado_fuentes.xlsx`, pero ahora se compara primero contra el workbook ya existente.
- si el contenido tabular de las hojas `resumen` y `columnas` ya coincide, el archivo no se vuelve a escribir.
- se normalizaron equivalencias de Excel que estaban rompiendo la deteccion:
  - cadena vacia vs celda en blanco
  - `0` vs `0.0`

Impacto esperado:

- evitar reserializacion espuria del XLSX en corridas consecutivas.

### `src/load.py`

- se migraron imports internos a `from src...`.
- se agrego preparacion y comparacion logica de `dim_comuna`, tabla de hechos y `metadata_fuentes` antes de reconstruir SQLite.
- si la base existente ya contiene exactamente los mismos datos esperados y pasa `PRAGMA quick_check`, no se resetea ni recarga.

Impacto esperado:

- evitar recrear `db/lab1_desigualdad.sqlite` en cada rerun cuando no hay cambios reales.

## 4. Validacion posterior

### Sintaxis

- `python -m compileall -q src`: OK

### Ejecucion principal

- `python src/main.py`: OK

### Ejecucion como modulo

- `python -m src.main`: OK

### Dataset final

Validacion ejecutada sobre `data/processed/desigualdad_comunal_final.csv`:

- existe: `True`
- filas: `32`
- esquema esperado de 12 columnas: `True`
- duplicados por `codigo_comuna`: `0`
- nulos en columnas criticas:
  - `codigo_comuna`: `0`
  - `nombre_comuna`: `0`
  - `poblacion`: `0`
  - `pobreza_ingresos_pct`: `0`
  - `areas_verdes_m2`: `0`
  - `ipp_miles_pesos`: `0`
  - `areas_verdes_m2_hab`: `0`
  - `ipp_pesos_hab`: `0`
- comunas unicas por `codigo_comuna`: `32`

### SQLite

Validacion ejecutada sobre `db/lab1_desigualdad.sqlite`:

- existe: `True`
- tablas detectadas: `['dim_comuna', 'fact_desigualdad_comunal', 'metadata_fuentes']`
- conteos:
  - `dim_comuna`: `32`
  - `fact_desigualdad_comunal`: `32`
  - `metadata_fuentes`: `4`
- join validado entre dimension y fact:
  - `join_count`: `32`
  - muestra:
    - `('13101', 'SANTIAGO', 3.8648)`
    - `('13102', 'CERRILLOS', 5.2287)`
    - `('13103', 'CERRO NAVIA', 6.0135)`

### Outputs

Se verifico existencia de 23 artefactos clave de Fase 7, 8 y 9.

- faltantes detectados: `[]`

## 5. Idempotencia

### Estado antes de corregir

- una corrida limpia dejaba dos artefactos binarios modificados:
  - `db/lab1_desigualdad.sqlite`
  - `outputs/perfilado_fuentes.xlsx`

### Causa identificada

- `src/load.py` siempre reseteaba y recargaba la base SQLite completa.
- `src/extract.py` siempre reescribia `outputs/perfilado_fuentes.xlsx`.
- en el caso del XLSX, la comparacion inicial tambien fallaba por equivalencias de representacion propias de Excel (`''` vs blank, `0` vs `0.0`).

### Estado despues de corregir

Secuencia validada:

1. se restauro el arbol a `HEAD` para los artefactos generados usados en la prueba.
2. se ejecuto `python src/main.py`.
3. se reviso `git status --short`.
4. se ejecuto inmediatamente `python -m src.main`.
5. se reviso nuevamente `git status --short`.

Resultado:

- despues de ambas corridas, Git solo mostro cambios intencionales en:
  - `README.md`
  - archivos `src/*.py` modificados por esta correccion
  - `src/__init__.py` nuevo
- no quedaron cambios adicionales en `outputs/perfilado_fuentes.xlsx`.
- no quedaron cambios adicionales en `db/lab1_desigualdad.sqlite`.

Conclusion:

- la reejecucion inmediata del pipeline quedo estable para los artefactos binarios que ensuciaban el repo.
- no quedan excepciones residuales documentadas para este escenario de rerun.

## 6. Riesgos y observaciones

- no se tocaron archivos en `data/raw/`.
- no se modifico la llave principal `codigo_comuna`.
- no se cambiaron joins hacia nombres crudos de comuna.
- no se reabrieron Fases 1 a 9 mas alla de validacion por ejecucion real y correcciones puntuales de consistencia.
- el ajuste de compatibilidad garantiza las dos formas pedidas de entrada al pipeline; no se extendio ese compromiso a la ejecucion directa de otros modulos individuales fuera de `main.py`, porque no era parte del problema reportado.
- desde el punto de vista tecnico, el repositorio queda consistente para avanzar a Fases 10, 11 y 12.
