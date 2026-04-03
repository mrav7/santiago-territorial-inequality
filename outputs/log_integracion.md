# Log de integracion

## Base maestra
- Archivo base: `data/raw/dim_comuna_base.csv`
- Filas iniciales: 32
- Columnas base conservadas para integracion: `codigo_comuna`, `nombre_comuna`.
- Llave de merge aplicada en toda la fase: `codigo_comuna`.

## Evidencia de merges
### Merge 1 - Poblacion comunal
- Archivo staging: `data/staging/poblacion_staging.csv`
- Tipo de merge: `left` con validacion `one_to_one`.
- Filas antes: 32
- Filas despues: 32
- Columnas incorporadas: poblacion, anio_poblacion
- Nulos relevantes despues del merge: poblacion=0
- Duplicados en staging por `codigo_comuna`: 0
- Duplicados en resultado por `codigo_comuna`: 0
- Comunas sin dato de esta fuente tras el merge: 0

### Merge 2 - Pobreza por ingresos
- Archivo staging: `data/staging/pobreza_staging.csv`
- Tipo de merge: `left` con validacion `one_to_one`.
- Filas antes: 32
- Filas despues: 32
- Columnas incorporadas: pobreza_ingresos_pct, anio_pobreza
- Nulos relevantes despues del merge: pobreza_ingresos_pct=0
- Duplicados en staging por `codigo_comuna`: 0
- Duplicados en resultado por `codigo_comuna`: 0
- Comunas sin dato de esta fuente tras el merge: 0

### Merge 3 - Areas verdes
- Archivo staging: `data/staging/areas_verdes_staging.csv`
- Tipo de merge: `left` con validacion `one_to_one`.
- Filas antes: 32
- Filas despues: 32
- Columnas incorporadas: areas_verdes_m2, anio_areas_verdes
- Nulos relevantes despues del merge: areas_verdes_m2=0
- Duplicados en staging por `codigo_comuna`: 0
- Duplicados en resultado por `codigo_comuna`: 0
- Comunas sin dato de esta fuente tras el merge: 0

### Merge 4 - Capacidad municipal
- Archivo staging: `data/staging/ingresos_staging.csv`
- Tipo de merge: `left` con validacion `one_to_one`.
- Filas antes: 32
- Filas despues: 32
- Columnas incorporadas: ipp_miles_pesos, anio_ingresos
- Nulos relevantes despues del merge: ipp_miles_pesos=0
- Duplicados en staging por `codigo_comuna`: 0
- Duplicados en resultado por `codigo_comuna`: 0
- Comunas sin dato de esta fuente tras el merge: 0

## Validacion final de integracion
- Filas finales: 32
- Columnas finales: 12
- `codigo_comuna` unico: si.
- Nulos relevantes en dataset final: poblacion=0, pobreza_ingresos_pct=0, areas_verdes_m2=0, ipp_miles_pesos=0, areas_verdes_m2_hab=0, ipp_pesos_hab=0.
- Infinitos detectados en metricas derivadas: areas_verdes_m2_hab=0, ipp_pesos_hab=0.
- `areas_verdes_m2_hab >= 0` cuando hay dato: si.
- `ipp_pesos_hab >= 0` cuando hay dato: si.
- Confirmacion: se mantuvieron 32 comunas y no se genero SQLite en esta fase.

## Alertas
- No se detectaron alertas de merge ni perdida de comunas.
