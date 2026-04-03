# Reporte de carga SQLite

## Insumo de carga
- Dataset final utilizado: `data/processed/desigualdad_comunal_final.csv`
- Validacion previa obligatoria: Fase 7 ejecutada y dataset marcado como apto para SQLite.
- Base SQLite generada: `db/lab1_desigualdad.sqlite`
- Tablas creadas: dim_comuna, fact_desigualdad_comunal, metadata_fuentes

## Validacion formal
- [OK] El archivo SQLite existe en la ruta esperada. (observado: db/lab1_desigualdad.sqlite; esperado: db/lab1_desigualdad.sqlite).
  Ruta estable del entregable final de Fase 8.
- [OK] La base abre correctamente y supera `PRAGMA quick_check`. (observado: ok; esperado: ok).
  Chequeo rapido de integridad del archivo SQLite.
- [OK] Existen las tablas esperadas en la base. (observado: dim_comuna, fact_desigualdad_comunal, metadata_fuentes; esperado: dim_comuna, fact_desigualdad_comunal, metadata_fuentes).
  Modelo fisico minimo requerido para la entrega.
- [OK] `dim_comuna` contiene 32 filas. (observado: 32; esperado: 32).
  Cobertura completa de comunas de la Provincia de Santiago.
- [OK] `fact_desigualdad_comunal` contiene 32 filas. (observado: 32; esperado: 32).
  Una fila por comuna en la tabla de hechos.
- [OK] `metadata_fuentes` se cargo segun el archivo fuente disponible. (observado: 4; esperado: 4).
  La tabla queda poblada con el contrato operativo de lectura.
- [OK] `dim_comuna` no tiene duplicados por `codigo_comuna`. (observado: 0; esperado: 0).
  Unicidad de la llave en la dimension.
- [OK] `fact_desigualdad_comunal` no tiene duplicados por `codigo_comuna`. (observado: 0; esperado: 0).
  Unicidad de la llave en la tabla de hechos.
- [OK] La cobertura entre `fact_desigualdad_comunal` y `dim_comuna` coincide exactamente. (observado: fact_sin_dim=0; dim_sin_fact=0; esperado: fact_sin_dim=0; dim_sin_fact=0).
  No hay codigos huerfanos entre ambas tablas.
- [OK] Las consultas obligatorias retornan resultados reproducibles. (observado: conteos=3; areas=5; pobreza=5; ipp=5; esperado: conteos=3; areas=5; pobreza=5; ipp=5).
  La base queda utilizable para consultas analiticas basicas.
- [OK] `PRAGMA table_info` devuelve estructura para todas las tablas. (observado: dim_comuna=5, fact_desigualdad_comunal=11, metadata_fuentes=13; esperado: todas las tablas con al menos 1 columna).
  La estructura fisica queda inspeccionable y documentada.

## Conteo de filas por tabla
- `dim_comuna`: 32
- `fact_desigualdad_comunal`: 32
- `metadata_fuentes`: 4

## Metadata de fuentes
- Metadata cargada: si
- Filas en metadata_fuentes: 4
- Estado metadata: ok

## Consultas obligatorias
### Top 5 comunas con menor `areas_verdes_m2_hab`
- 1. CONCHALI (13104): 0.603247
- 2. CERRILLOS (13102): 0.878035
- 3. INDEPENDENCIA (13108): 0.878941
- 4. LA CISTERNA (13109): 0.904776
- 5. SAN MIGUEL (13130): 1.154347

### Top 5 comunas con mayor `pobreza_ingresos_pct`
- 1. LA PINTANA (13112): 9.2938
- 2. SAN RAMON (13131): 6.8821
- 3. LO ESPEJO (13116): 6.7817
- 4. EL BOSQUE (13105): 6.1982
- 5. CONCHALI (13104): 6.0799

### Top 5 comunas con menor `ipp_pesos_hab`
- 1. CERRO NAVIA (13103): 27701.980354
- 2. LA PINTANA (13112): 38281.739358
- 3. LO PRADO (13117): 39312.805346
- 4. EL BOSQUE (13105): 45941.619379
- 5. LA GRANJA (13111): 47063.353627

## Estructura de tablas
### dim_comuna
- `codigo_comuna` TEXT (pk=1, notnull=0, default=None)
- `nombre_comuna` TEXT (pk=0, notnull=1, default=None)
- `provincia` TEXT (pk=0, notnull=1, default=None)
- `region` TEXT (pk=0, notnull=1, default=None)
- `fuente_referencia` TEXT (pk=0, notnull=1, default=None)

### fact_desigualdad_comunal
- `codigo_comuna` TEXT (pk=1, notnull=0, default=None)
- `poblacion` INTEGER (pk=0, notnull=0, default=None)
- `anio_poblacion` INTEGER (pk=0, notnull=0, default=None)
- `pobreza_ingresos_pct` REAL (pk=0, notnull=0, default=None)
- `anio_pobreza` INTEGER (pk=0, notnull=0, default=None)
- `areas_verdes_m2` INTEGER (pk=0, notnull=0, default=None)
- `anio_areas_verdes` INTEGER (pk=0, notnull=0, default=None)
- `ipp_miles_pesos` INTEGER (pk=0, notnull=0, default=None)
- `anio_ingresos` INTEGER (pk=0, notnull=0, default=None)
- `areas_verdes_m2_hab` REAL (pk=0, notnull=0, default=None)
- `ipp_pesos_hab` REAL (pk=0, notnull=0, default=None)

### metadata_fuentes
- `id_fuente` TEXT (pk=1, notnull=0, default=None)
- `nombre_fuente` TEXT (pk=0, notnull=1, default=None)
- `institucion` TEXT (pk=0, notnull=1, default=None)
- `url` TEXT (pk=0, notnull=1, default=None)
- `fecha_descarga` TEXT (pk=0, notnull=1, default=None)
- `formato` TEXT (pk=0, notnull=1, default=None)
- `anio_referencia` INTEGER (pk=0, notnull=0, default=None)
- `variable_principal` TEXT (pk=0, notnull=1, default=None)
- `archivo_origen` TEXT (pk=0, notnull=1, default=None)
- `archivo_logico` TEXT (pk=0, notnull=1, default=None)
- `hoja` TEXT (pk=0, notnull=1, default=None)
- `skiprows` INTEGER (pk=0, notnull=0, default=None)
- `observaciones` TEXT (pk=0, notnull=0, default=None)

## Cierre
- La base queda consultable desde SQLite y preserva `codigo_comuna` como llave central.
- La combinacion `dim_comuna` + `fact_desigualdad_comunal` reproduce el dataset final validado.
- `metadata_fuentes` documenta el contrato operativo de las fuentes utilizadas en el ETL.
