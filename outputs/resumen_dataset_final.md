# Resumen del dataset final

## Dataset generado
- Archivo: `data/processed/desigualdad_comunal_final.csv`
- Filas: 32
- Columnas: 12
- Unidad de analisis: una fila = una comuna.
- Cobertura: Provincia de Santiago.

## Columnas finales
- `codigo_comuna`: Llave maestra comunal oficial del proyecto.
- `nombre_comuna`: Nombre oficial de la comuna segun `dim_comuna_base.csv`.
- `poblacion`: Poblacion comunal censada usada para el denominador de indicadores por habitante.
- `anio_poblacion`: Anio de referencia de la poblacion comunal.
- `pobreza_ingresos_pct`: Porcentaje de personas en situacion de pobreza por ingresos.
- `anio_pobreza`: Anio de referencia de la pobreza por ingresos.
- `areas_verdes_m2`: Superficie total de areas verdes comunales en metros cuadrados.
- `anio_areas_verdes`: Anio de referencia de las areas verdes.
- `ipp_miles_pesos`: Ingresos propios permanentes comunales en miles de pesos nominales.
- `anio_ingresos`: Anio de referencia del IPP.
- `areas_verdes_m2_hab`: Metricas derivada: `areas_verdes_m2 / poblacion`. Se deja `NaN` si falta algun dato o si `poblacion <= 0`.
- `ipp_pesos_hab`: Metrica derivada: `(ipp_miles_pesos * 1000) / poblacion`. Se deja `NaN` si falta algun dato o si `poblacion <= 0`.

## Anios de referencia usados
- `anio_poblacion = 2024`.
- `anio_pobreza = 2022`.
- `anio_areas_verdes = 2024`.
- `anio_ingresos = 2024`.

## Observaciones metodologicas
- `nombre_comuna` proviene exclusivamente de `dim_comuna_base.csv`.
- Los cuatro merges se hicieron como `left` sobre `codigo_comuna` y con control de cardinalidad `one_to_one`.
- No se realizaron imputaciones. Los `NaN` corresponden a faltantes reales en staging o a divisiones invalidas por `poblacion` nula/no positiva.
- El dataset queda preparado para validacion de calidad del resultado final en Fase 7.
- Este dataset soporta analisis comparativo y descriptivo; no permite afirmar causalidad.

## Alertas observadas
- No se detectaron alertas operativas durante la integracion.
