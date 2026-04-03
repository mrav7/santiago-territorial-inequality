# Resumen de transformaciones a staging

Este documento resume la trazabilidad y las reglas aplicadas en Fase 4 y Fase 5.

## Fuente A - SINIM - Areas Verdes
- Archivo raw origen: `data/raw/datos_municipales_20260402222841_Sin-Corrección-Monetaria.xls`
- Fuente logica / archivo logico: `sinim_areas_verdes_2024_rm.xls`
- Archivo staging generado: `data/staging/areas_verdes_staging.csv`
- Filas antes: 52
- Filas despues: 32
- Fuera de universo detectados: 20
- Filas sin codigo comunal valido excluidas: 0
- Duplicados por `codigo_comuna` en staging: 0
- Columnas originales consideradas: codigo_comuna, nombre_comuna, mmpqc_2024, mmpzc_2024
- Columnas finales conservadas: codigo_comuna, nombre_comuna, mmpqc_2024, mmpzc_2024, areas_verdes_m2
- Renombres realizados: Sin renombre en columnas base; se crea `areas_verdes_m2`.
- Tipos convertidos: `codigo_comuna` -> string de 5 digitos.; `mmpqc_2024` -> Int64.; `mmpzc_2024` -> Int64.; `areas_verdes_m2` -> Int64.
- Valores especiales tratados: `No Aplica` -> 0 en componentes de areas verdes.; `No Recepcionado` -> NaN.
- Filtros aplicados: Filtrado al universo final usando `dim_comuna_base.csv` y `codigo_comuna`.; Exclusion de registros sin codigo comunal valido.; Estandarizacion de `nombre_comuna` contra la dimension maestra.
- Validaciones ejecutadas:
  [OK] Las columnas finales coinciden con el esquema esperado.
  [OK] La tabla contiene 32 comunas del universo final.
  [OK] `codigo_comuna` es unico en la salida staging.
  [OK] No hay nulos en las columnas clave.
  [OK] `codigo_comuna` quedo como string consistente de 5 digitos.
  [OK] La cobertura comunal coincide exactamente con la dimension maestra.
  [OK] `nombre_comuna` quedo estandarizado contra la base maestra.
  [OK] Se cumple la validacion de rango: areas_verdes_m2 >= 0.
  [OK] Archivo staging exportado: data/staging/areas_verdes_staging.csv.
- Observaciones o limitaciones pendientes:
  La suma total exige ambas componentes numericas; si una queda nula, `areas_verdes_m2` permanece nulo.

## Fuente B - SINIM - Capacidad Municipal
- Archivo raw origen: `data/raw/datos_municipales_20260402223904_Sin-Corrección-Monetaria.xls`
- Fuente logica / archivo logico: `sinim_capacidad_municipal_ipp_2024_rm.xls`
- Archivo staging generado: `data/staging/ingresos_staging.csv`
- Filas antes: 52
- Filas despues: 32
- Fuera de universo detectados: 20
- Filas sin codigo comunal valido excluidas: 0
- Duplicados por `codigo_comuna` en staging: 0
- Columnas originales consideradas: codigo_comuna, nombre_comuna, iadm41_2024
- Columnas finales conservadas: codigo_comuna, nombre_comuna, ipp_miles_pesos
- Renombres realizados: `iadm41_2024` -> `ipp_miles_pesos`.
- Tipos convertidos: `codigo_comuna` -> string de 5 digitos.; `ipp_miles_pesos` -> Int64.
- Valores especiales tratados: No se detectaron valores especiales dentro del universo final en la variable IPP.
- Filtros aplicados: Filtrado al universo final usando `dim_comuna_base.csv` y `codigo_comuna`.; Exclusion de registros sin codigo comunal valido.; Estandarizacion de `nombre_comuna` contra la dimension maestra.
- Validaciones ejecutadas:
  [OK] Las columnas finales coinciden con el esquema esperado.
  [OK] La tabla contiene 32 comunas del universo final.
  [OK] `codigo_comuna` es unico en la salida staging.
  [OK] No hay nulos en las columnas clave.
  [OK] `codigo_comuna` quedo como string consistente de 5 digitos.
  [OK] La cobertura comunal coincide exactamente con la dimension maestra.
  [OK] `nombre_comuna` quedo estandarizado contra la base maestra.
  [OK] Se cumple la validacion de rango: ipp_miles_pesos >= 0.
  [OK] Archivo staging exportado: data/staging/ingresos_staging.csv.
- Observaciones o limitaciones pendientes:
  La unidad se conserva como miles de pesos nominales 2024, consistente con metadata y el descriptor del archivo.

## Fuente C - Observatorio Social - Pobreza por Ingresos
- Archivo raw origen: `data/raw/estimaciones_tasa_pobreza_ingresos_comunas_2022.xlsx`
- Fuente logica / archivo logico: `observatorio_social_pobreza_ingresos_2022.xlsx`
- Archivo staging generado: `data/staging/pobreza_staging.csv`
- Filas antes: 351
- Filas despues: 32
- Fuera de universo detectados: 313
- Filas sin codigo comunal valido excluidas: 6
- Duplicados por `codigo_comuna` en staging: 0
- Columnas originales consideradas: Código, Nombre comuna, Porcentaje de personas en situación de pobreza por ingresos 2022
- Columnas finales conservadas: codigo_comuna, nombre_comuna, pobreza_ingresos_pct
- Renombres realizados: `Código` -> `codigo_comuna`.; `Nombre comuna` -> `nombre_comuna`.; `Porcentaje de personas en situación de pobreza por ingresos 2022` -> `pobreza_ingresos_pct`.
- Tipos convertidos: `codigo_comuna` -> string de 5 digitos.; `pobreza_ingresos_pct` -> Float64 en escala 0-100.
- Valores especiales tratados: Se excluyen filas de nota, blancos y residuos textuales al exigir `codigo_comuna` valido.
- Filtros aplicados: Exclusion de filas sin codigo comunal valido.; Filtrado al universo final usando `dim_comuna_base.csv` y `codigo_comuna`.; Estandarizacion de `nombre_comuna` contra la dimension maestra.
- Validaciones ejecutadas:
  [OK] Las columnas finales coinciden con el esquema esperado.
  [OK] La tabla contiene 32 comunas del universo final.
  [OK] `codigo_comuna` es unico en la salida staging.
  [OK] No hay nulos en las columnas clave.
  [OK] `codigo_comuna` quedo como string consistente de 5 digitos.
  [OK] La cobertura comunal coincide exactamente con la dimension maestra.
  [OK] `nombre_comuna` quedo estandarizado contra la base maestra.
  [OK] Se cumple la validacion de rango: pobreza_ingresos_pct entre 0 y 100.
  [OK] Archivo staging exportado: data/staging/pobreza_staging.csv.
- Observaciones o limitaciones pendientes:
  La variable original venia como proporcion 0-1 y se transformo a porcentaje 0-100.

## Fuente D - Censo 2024 - Poblacion Comunal
- Archivo raw origen: `data/raw/D1_Poblacion-censada-por-sexo-y-edad-en-grupos-quinquenales.xlsx`
- Fuente logica / archivo logico: `ine_poblacion_comunal_2024.xlsx`
- Archivo staging generado: `data/staging/poblacion_staging.csv`
- Filas antes: 349
- Filas despues: 32
- Fuera de universo detectados: 315
- Filas sin codigo comunal valido excluidas: 2
- Duplicados por `codigo_comuna` en staging: 0
- Columnas originales consideradas: Código comuna, Comuna, Población censada
- Columnas finales conservadas: codigo_comuna, nombre_comuna, poblacion
- Renombres realizados: `Código comuna` -> `codigo_comuna`.; `Comuna` -> `nombre_comuna`.; `Población censada` -> `poblacion`.
- Tipos convertidos: `codigo_comuna` -> string de 5 digitos.; `poblacion` -> Int64.
- Valores especiales tratados: Se excluyen la fila agregada `País`, filas en blanco y notas al exigir `codigo_comuna` valido y filtrar por el universo final.
- Filtros aplicados: Exclusion de filas sin codigo comunal valido.; Filtrado al universo final usando `dim_comuna_base.csv` y `codigo_comuna`.; Estandarizacion de `nombre_comuna` contra la dimension maestra.
- Validaciones ejecutadas:
  [OK] Las columnas finales coinciden con el esquema esperado.
  [OK] La tabla contiene 32 comunas del universo final.
  [OK] `codigo_comuna` es unico en la salida staging.
  [OK] No hay nulos en las columnas clave.
  [OK] `codigo_comuna` quedo como string consistente de 5 digitos.
  [OK] La cobertura comunal coincide exactamente con la dimension maestra.
  [OK] `nombre_comuna` quedo estandarizado contra la base maestra.
  [OK] Se cumple la validacion de rango: poblacion > 0.
  [OK] Archivo staging exportado: data/staging/poblacion_staging.csv.
- Observaciones o limitaciones pendientes:
  La fuente original contiene columnas adicionales de sexo y razon hombre-mujer, pero en esta fase solo se conserva `poblacion`.

## Estado
- Las tablas staging quedan listas para merge posterior, pero aun no existe dataset final integrado.
- No se genera SQLite en esta fase.
