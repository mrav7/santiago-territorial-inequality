# Conflictos detectados en Fase 2

## Resumen ejecutivo
- Las cuatro fuentes se leen desde `data/raw/` usando `metadata_fuentes.csv` como contrato operativo.
- Las fuentes A y B requirieron parser especial para SpreadsheetML/XML 2003; C y D se leen con `pandas.read_excel()` respetando `hoja` y `skiprows` del metadata.
- El diagnostico confirma que la llave estable para la unidad de analisis debe ser `codigo_comuna`; los nombres de comuna cambian en mayusculas, tildes y estilo de escritura entre fuentes.
- Persisten filas fuera de alcance, filas de notas/totales y celdas especiales que deben resolverse en Fase 3/Fase 5.

## Conflictos transversales
- Fuente A: hay 6 diferencias de nombre exacto frente a `dim_comuna_base.csv`. Ejemplos: 13104: CONCHALI -> CONCHALÍ; 13106: ESTACION CENTRAL -> ESTACIÓN CENTRAL; 13119: MAIPU -> MAIPÚ; 13122: PEÑALOLEN -> PEÑALOLÉN; 13129: SAN JOAQUIN -> SAN JOAQUÍN.
- Fuente B: hay 6 diferencias de nombre exacto frente a `dim_comuna_base.csv`. Ejemplos: 13104: CONCHALI -> CONCHALÍ; 13106: ESTACION CENTRAL -> ESTACIÓN CENTRAL; 13119: MAIPU -> MAIPÚ; 13122: PEÑALOLEN -> PEÑALOLÉN; 13129: SAN JOAQUIN -> SAN JOAQUÍN.
- Fuente C: hay 32 diferencias de nombre exacto frente a `dim_comuna_base.csv`. Ejemplos: 13101: SANTIAGO -> Santiago; 13102: CERRILLOS -> Cerrillos; 13103: CERRO NAVIA -> Cerro Navia; 13104: CONCHALI -> Conchalí; 13105: EL BOSQUE -> El Bosque.
- Fuente D: hay 32 diferencias de nombre exacto frente a `dim_comuna_base.csv`. Ejemplos: 13101: SANTIAGO -> Santiago; 13102: CERRILLOS -> Cerrillos; 13103: CERRO NAVIA -> Cerro Navia; 13104: CONCHALI -> Conchalí; 13105: EL BOSQUE -> El Bosque.
- Priorizar `codigo_comuna` sobre `nombre_comuna` en joins y validaciones; las variantes de nombre son compatibles solo despues de normalizacion de mayusculas y tildes.
- Todas las fuentes exceden el alcance final de la Provincia de Santiago: deben filtrarse usando `dim_comuna_base.csv` antes de integrar.

## Fuente A - SINIM - Areas Verdes
- Archivo: `data/raw/datos_municipales_20260402222841_Sin-Corrección-Monetaria.xls`
- Parser aplicado: `spreadsheetml_xml_2003`
- Lectura operativa: hoja `Hoja1` con `skiprows=2`.
- Cobertura detectada por codigo: 52 codigos validos; 32 comunas de la Provincia de Santiago y 20 registros fuera de alcance.
- El archivo trae encabezado extendido previo a la tabla util. Se reconstruyeron columnas utilizables a partir de la fila descriptiva y la fila de encabezado.
- Se detectaron valores especiales no numericos en columnas operativamente numericas: No Aplica=3, No Recepcionado=4.
- Diferencias de nombre exacto respecto a la dimension base: 6. Ejemplos: 13104: CONCHALI -> CONCHALÍ; 13106: ESTACION CENTRAL -> ESTACIÓN CENTRAL; 13119: MAIPU -> MAIPÚ; 13122: PEÑALOLEN -> PEÑALOLÉN; 13129: SAN JOAQUIN -> SAN JOAQUÍN.

## Fuente B - SINIM - Capacidad Municipal
- Archivo: `data/raw/datos_municipales_20260402223904_Sin-Corrección-Monetaria.xls`
- Parser aplicado: `spreadsheetml_xml_2003`
- Lectura operativa: hoja `Hoja1` con `skiprows=2`.
- Cobertura detectada por codigo: 52 codigos validos; 32 comunas de la Provincia de Santiago y 20 registros fuera de alcance.
- El archivo trae encabezado extendido previo a la tabla util. Se reconstruyeron columnas utilizables a partir de la fila descriptiva y la fila de encabezado.
- Diferencias de nombre exacto respecto a la dimension base: 6. Ejemplos: 13104: CONCHALI -> CONCHALÍ; 13106: ESTACION CENTRAL -> ESTACIÓN CENTRAL; 13119: MAIPU -> MAIPÚ; 13122: PEÑALOLEN -> PEÑALOLÉN; 13129: SAN JOAQUIN -> SAN JOAQUÍN.

## Fuente C - Observatorio Social - Pobreza por Ingresos
- Archivo: `data/raw/estimaciones_tasa_pobreza_ingresos_comunas_2022.xlsx`
- Parser aplicado: `pandas_read_excel`
- Lectura operativa: hoja `Estimaciones` con `skiprows=2`.
- Cobertura detectada por codigo: 345 codigos validos; 32 comunas de la Provincia de Santiago y 313 registros fuera de alcance.
- Se detectaron 6 filas en blanco o de nota que deben excluirse antes de tipificar o integrar.
- La variable de pobreza viene como proporcion entre 0 y 1, no como porcentaje 0-100. Esa conversion debe tratarse en la fase de transformacion.
- Diferencias de nombre exacto respecto a la dimension base: 32. Ejemplos: 13101: SANTIAGO -> Santiago; 13102: CERRILLOS -> Cerrillos; 13103: CERRO NAVIA -> Cerro Navia; 13104: CONCHALI -> Conchalí; 13105: EL BOSQUE -> El Bosque.

## Fuente D - Censo 2024 - Poblacion Comunal
- Archivo: `data/raw/D1_Poblacion-censada-por-sexo-y-edad-en-grupos-quinquenales.xlsx`
- Parser aplicado: `pandas_read_excel`
- Lectura operativa: hoja `2` con `skiprows=3`.
- Cobertura detectada por codigo: 347 codigos validos; 32 comunas de la Provincia de Santiago y 315 registros fuera de alcance.
- Se detectaron 2 filas en blanco o de nota que deben excluirse antes de tipificar o integrar.
- La hoja incluye 1 fila total/agrupadora (`País`) que no pertenece a la unidad de analisis comunal.
- Diferencias de nombre exacto respecto a la dimension base: 32. Ejemplos: 13101: SANTIAGO -> Santiago; 13102: CERRILLOS -> Cerrillos; 13103: CERRO NAVIA -> Cerro Navia; 13104: CONCHALI -> Conchalí; 13105: EL BOSQUE -> El Bosque.

## Listo para Fase 3 y Fase 5
- Filtrar las cuatro fuentes por `codigo_comuna` usando `dim_comuna_base.csv`.
- Excluir filas de notas, filas totalmente vacias y totales antes de convertir tipos.
- Convertir valores especiales como `No Aplica` y `No Recepcionado` a nulos controlados.
- Mantener los nombres de comuna solo como apoyo de validacion y presentacion; no como llave de integracion.
