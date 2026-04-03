# Reporte de validacion final

## Dataset validado
- Archivo: `data/processed/desigualdad_comunal_final.csv`
- Filas observadas: 32
- Columnas observadas: 12
- Estado global: APTO PARA FASE 8

## Chequeos ejecutados
- [OK] El dataset final contiene exactamente las columnas esperadas. (observado: codigo_comuna | nombre_comuna | poblacion | anio_poblacion | pobreza_ingresos_pct | anio_pobreza | areas_verdes_m2 | anio_areas_verdes | ipp_miles_pesos | anio_ingresos | areas_verdes_m2_hab | ipp_pesos_hab; esperado: codigo_comuna | nombre_comuna | poblacion | anio_poblacion | pobreza_ingresos_pct | anio_pobreza | areas_verdes_m2 | anio_areas_verdes | ipp_miles_pesos | anio_ingresos | areas_verdes_m2_hab | ipp_pesos_hab).
  Sin diferencias de esquema.
- [OK] Existe una sola fila por comuna. (observado: filas=32; comunas_unicas=32; esperado: filas == comunas_unicas).
  Sin multiplicacion de filas por comuna.
- [OK] `codigo_comuna` no contiene nulos. (observado: 0; esperado: 0).
  Llave primaria completa.
- [OK] `codigo_comuna` mantiene formato string de 5 digitos. (observado: OK; esperado: regex ^\d{5}$).
  Todos los codigos cumplen el formato esperado.
- [OK] `codigo_comuna` es unico. (observado: 0; esperado: 0).
  Sin duplicados por llave.
- [OK] El dataset final contiene exactamente 32 comunas. (observado: 32; esperado: 32).
  Cobertura total observada.
- [OK] La cobertura comunal coincide con `dim_comuna_base.csv`. (observado: faltantes=[]; extras=[]; esperado: sin faltantes ni extras).
  Cobertura exacta contra la base maestra.
- [OK] `nombre_comuna` coincide con la base maestra. (observado: 0; esperado: 0).
  Los nombres finales preservan la base maestra.
- [OK] Las columnas numericas son convertibles a tipo numerico razonable. (observado: poblacion=0; anio_poblacion=0; pobreza_ingresos_pct=0; anio_pobreza=0; areas_verdes_m2=0; anio_areas_verdes=0; ipp_miles_pesos=0; anio_ingresos=0; areas_verdes_m2_hab=0; ipp_pesos_hab=0; esperado: 0 errores de conversion).
  Todas las columnas numericas son convertibles.
- [OK] Los anios de referencia permanecen consistentes con Fase 6. (observado: anio_poblacion=[2024]; anio_pobreza=[2022]; anio_areas_verdes=[2024]; anio_ingresos=[2024]; esperado: anio_poblacion=[2024]; anio_pobreza=[2022]; anio_areas_verdes=[2024]; anio_ingresos=[2024]).
  Anios de referencia consistentes.
- [OK] `poblacion` es estrictamente mayor que 0. (observado: 0; esperado: 0).
  Toda la poblacion es positiva.
- [OK] `pobreza_ingresos_pct` queda entre 0 y 100 cuando hay dato. (observado: 0; esperado: 0).
  La variable de pobreza esta dentro de rango.
- [OK] `areas_verdes_m2` es no negativa cuando hay dato. (observado: 0; esperado: 0).
  Sin areas verdes negativas.
- [OK] `ipp_miles_pesos` es no negativo cuando hay dato. (observado: 0; esperado: 0).
  Sin IPP negativos.
- [OK] `areas_verdes_m2_hab` no contiene infinitos. (observado: 0; esperado: 0).
  Sin infinitos en areas verdes por habitante.
- [OK] `ipp_pesos_hab` no contiene infinitos. (observado: 0; esperado: 0).
  Sin infinitos en IPP por habitante.
- [OK] El dataset final es apto para pasar a Fase 8 / carga a SQLite. (observado: APTO; esperado: APTO).
  El dataset final cumple los criterios estructurales y de integridad requeridos.

## Nulos por columna
- `codigo_comuna`: 0
- `nombre_comuna`: 0
- `poblacion`: 0
- `anio_poblacion`: 0
- `pobreza_ingresos_pct`: 0
- `anio_pobreza`: 0
- `areas_verdes_m2`: 0
- `anio_areas_verdes`: 0
- `ipp_miles_pesos`: 0
- `anio_ingresos`: 0
- `areas_verdes_m2_hab`: 0
- `ipp_pesos_hab`: 0

## Convertibilidad numerica
- `poblacion`: 0 errores de conversion
- `anio_poblacion`: 0 errores de conversion
- `pobreza_ingresos_pct`: 0 errores de conversion
- `anio_pobreza`: 0 errores de conversion
- `areas_verdes_m2`: 0 errores de conversion
- `anio_areas_verdes`: 0 errores de conversion
- `ipp_miles_pesos`: 0 errores de conversion
- `anio_ingresos`: 0 errores de conversion
- `areas_verdes_m2_hab`: 0 errores de conversion
- `ipp_pesos_hab`: 0 errores de conversion

## Cobertura comunal
- Codigos faltantes respecto a base maestra: []
- Codigos extra respecto a base maestra: []

## Observacion metodologica
- Esta validacion confirma integridad estructural y consistencia descriptiva del dataset final.
- El uso analitico sigue siendo comparativo y descriptivo; no habilita inferencias causales.
