# Resumen Fase 4 y Fase 5

## Fase 4 - Staging reproducible
- La extraccion queda materializada como tablas crudas parseadas, una por fuente, sin integrar aun el dataset final.
- Los archivos de staging preservan la estructura leida desde cada fuente y sirven como base reproducible para las transformaciones posteriores.

- Fuente A: `data/staging/fuente_a_sinim_areas_verdes.csv` con 52 filas y 4 columnas.
- Fuente B: `data/staging/fuente_b_sinim_capacidad_municipal.csv` con 52 filas y 3 columnas.
- Fuente C: `data/staging/fuente_c_pobreza_ingresos.csv` con 351 filas y 10 columnas.
- Fuente D: `data/staging/fuente_d_poblacion_comunal.csv` con 349 filas y 10 columnas.

## Fase 5 - Reglas de transformacion
- Fuente A: `No Aplica` se interpreta como 0 solo para componentes de areas verdes; `No Recepcionado` permanece como nulo. El total se calcula como parques + plazas.
- Fuente B: el IPP se conserva en miles de pesos nominales 2024.
- Fuente C: las tasas de pobreza pasan de proporcion 0-1 a porcentaje 0-100.
- Fuente D: la tabla comunal queda filtrada al universo final de 32 comunas y se excluyen filas agregadas o notas al trabajar por `codigo_comuna`.

## Tablas limpias listas para merge
- Fuente A: `data/processed/fuente_a_areas_verdes_limpia.csv` con 32 filas y 5 columnas. Estado=OK.
- Fuente B: `data/processed/fuente_b_capacidad_municipal_limpia.csv` con 32 filas y 3 columnas. Estado=OK.
- Fuente C: `data/processed/fuente_c_pobreza_ingresos_limpia.csv` con 32 filas y 7 columnas. Estado=OK.
- Fuente D: `data/processed/fuente_d_poblacion_limpia.csv` con 32 filas y 6 columnas. Estado=OK.

## Validacion de salida
- Fuente A:
  [OK] La tabla tiene el esquema esperado.
  [OK] La tabla contiene 32 filas, una por comuna objetivo.
  [OK] `codigo_comuna` es unico en la tabla limpia.
  [OK] La cobertura comunal coincide exactamente con la dimension maestra.
  [OK] `nombre_comuna` quedo estandarizado contra la dimension maestra.
  [OK] Archivo exportado: data/processed/fuente_a_areas_verdes_limpia.csv.
  [OK] `areas_verdes_parques_m2_2024` no contiene valores negativos.
  [OK] `areas_verdes_plazas_m2_2024` no contiene valores negativos.
  [OK] `areas_verdes_total_m2_2024` no contiene valores negativos.
  [OK] El total de areas verdes coincide con la suma de parques y plazas.
- Fuente B:
  [OK] La tabla tiene el esquema esperado.
  [OK] La tabla contiene 32 filas, una por comuna objetivo.
  [OK] `codigo_comuna` es unico en la tabla limpia.
  [OK] La cobertura comunal coincide exactamente con la dimension maestra.
  [OK] `nombre_comuna` quedo estandarizado contra la dimension maestra.
  [OK] Archivo exportado: data/processed/fuente_b_capacidad_municipal_limpia.csv.
  [OK] `ipp_miles_pesos_2024` no contiene valores negativos.
- Fuente C:
  [OK] La tabla tiene el esquema esperado.
  [OK] La tabla contiene 32 filas, una por comuna objetivo.
  [OK] `codigo_comuna` es unico en la tabla limpia.
  [OK] La cobertura comunal coincide exactamente con la dimension maestra.
  [OK] `nombre_comuna` quedo estandarizado contra la dimension maestra.
  [OK] Archivo exportado: data/processed/fuente_c_pobreza_ingresos_limpia.csv.
  [OK] Los conteos de poblacion y pobreza son no negativos.
  [OK] Las tasas de pobreza quedaron expresadas como porcentaje 0-100.
  [OK] El porcentaje puntual queda dentro del intervalo inferior/superior.
- Fuente D:
  [OK] La tabla tiene el esquema esperado.
  [OK] La tabla contiene 32 filas, una por comuna objetivo.
  [OK] `codigo_comuna` es unico en la tabla limpia.
  [OK] La cobertura comunal coincide exactamente con la dimension maestra.
  [OK] `nombre_comuna` quedo estandarizado contra la dimension maestra.
  [OK] Archivo exportado: data/processed/fuente_d_poblacion_limpia.csv.
  [OK] Los conteos poblacionales son no negativos.
  [OK] `hombres_2024 + mujeres_2024` coincide con la poblacion censada.
  [OK] `razon_hombre_mujer_2024` contiene valores positivos.

## Estado del proyecto
- Sigue vigente la homologacion comunal de `outputs/resumen_homologacion.md` como soporte de trazabilidad.
- No se integra aun el dataset final comunal.
- No se carga aun ningun archivo SQLite.
