# Analisis exploratorio Fase 9

## Insumos y consistencia
- Dataset canonico analizado: `data/processed/desigualdad_comunal_final.csv`.
- Base SQLite contrastada: `db/lab1_desigualdad.sqlite`.
- Filas CSV vs SQLite: 32 vs 32.
- Cobertura exclusiva CSV: [].
- Cobertura exclusiva SQLite: [].
- Consistencia global CSV/SQLite: OK.
- Fuente de verdad para Fase 9: `data/processed/desigualdad_comunal_final.csv`; SQLite se usa como validacion de persistencia y consulta.

## Metodologia analitica
- Los rankings obligatorios se construyen con orden explicito ascendente o descendente segun el sentido de cada variable.
- Para cruces de rezago se usan quintiles por variable.
- `areas_verdes_m2_hab`: menor valor = peor situacion; el peor quintil se codifica como 5.
- `pobreza_ingresos_pct`: mayor valor = peor situacion; el peor quintil se codifica como 5.
- `ipp_pesos_hab`: menor valor = peor situacion; el peor quintil se codifica como 5.
- `indice_rezago_territorial` es una construccion analitica auxiliar: suma de los tres quintiles de rezago. Mayor valor = mayor rezago relativo observado.
- El analisis es descriptivo y comparativo; no permite inferir causalidad.

## Notas metodologicas para comunicacion
- `indice_rezago_territorial` es un apoyo descriptivo de Fase 9 y no una variable oficial de fuente.
- Los hallazgos no permiten inferencias causales; solo describen patrones observados entre comunas.
- QUILICURA aparece como outlier plausible en `areas_verdes_m2_hab` y debe interpretarse como caso especial al leer tablas y graficos.
- El scatter de pobreza y areas verdes usa escala logaritmica en el eje X para mantener visible el resto de las comunas sin ocultar ese caso extremo.

## Rankings obligatorios
### Top 5 comunas con menos `areas_verdes_m2_hab` (orden ascendente)
- 1. CONCHALI (13104): 0.603247
- 2. CERRILLOS (13102): 0.878035
- 3. INDEPENDENCIA (13108): 0.878941
- 4. LA CISTERNA (13109): 0.904776
- 5. SAN MIGUEL (13130): 1.154347

### Top 5 comunas con mas `areas_verdes_m2_hab` (orden descendente)
- 1. QUILICURA (13125): 3931.614773
- 2. LA REINA (13113): 21.734172
- 3. PROVIDENCIA (13123): 20.172865
- 4. PEÑALOLEN (13122): 13.012166
- 5. MAIPU (13119): 7.979950

### Top 5 comunas con mayor `pobreza_ingresos_pct` (orden descendente)
- 1. LA PINTANA (13112): 9.2938
- 2. SAN RAMON (13131): 6.8821
- 3. LO ESPEJO (13116): 6.7817
- 4. EL BOSQUE (13105): 6.1982
- 5. CONCHALI (13104): 6.0799

### Top 5 comunas con menor `pobreza_ingresos_pct` (orden ascendente)
- 1. VITACURA (13132): 0.8910
- 2. LO BARNECHEA (13115): 0.9028
- 3. LAS CONDES (13114): 0.9093
- 4. PROVIDENCIA (13123): 1.3219
- 5. ÑUÑOA (13120): 1.4888

### Top 5 comunas con menor `ipp_pesos_hab` (orden ascendente)
- 1. CERRO NAVIA (13103): 27701.980354
- 2. LA PINTANA (13112): 38281.739358
- 3. LO PRADO (13117): 39312.805346
- 4. EL BOSQUE (13105): 45941.619379
- 5. LA GRANJA (13111): 47063.353627

### Top 5 comunas con mayor `ipp_pesos_hab` (orden descendente)
- 1. LO BARNECHEA (13115): 1048997.007636
- 2. VITACURA (13132): 1001090.685027
- 3. LAS CONDES (13114): 743724.158658
- 4. PROVIDENCIA (13123): 697639.671052
- 5. HUECHURABA (13107): 424803.227644

## Cruces descriptivos
- Peor quintil simultaneo de pobreza y areas verdes por habitante: CONCHALI.
- Peor quintil simultaneo de pobreza e IPP por habitante: LA PINTANA, SAN RAMON, LO ESPEJO, EL BOSQUE, LA GRANJA, CERRO NAVIA.
- Rezagadas en al menos dos dimensiones: LO ESPEJO, EL BOSQUE, CONCHALI, LA PINTANA, SAN RAMON, LA GRANJA, CERRO NAVIA.

## Hallazgos reutilizables
- Se observa que las menores disponibilidades relativas de areas verdes se concentran en CONCHALI, CERRILLOS, INDEPENDENCIA, LA CISTERNA, SAN MIGUEL.
- Las mayores tasas observadas de pobreza por ingresos aparecen en LA PINTANA, SAN RAMON, LO ESPEJO, EL BOSQUE, CONCHALI.
- Los menores niveles de IPP por habitante aparecen en CERRO NAVIA, LA PINTANA, LO PRADO, EL BOSQUE, LA GRANJA.
- El cruce descriptivo muestra que CONCHALI combinan rezago en pobreza y areas verdes, mientras que LA PINTANA, SAN RAMON, LO ESPEJO, EL BOSQUE, LA GRANJA, CERRO NAVIA combinan rezago en pobreza e IPP por habitante.
- Las comunas con rezago critico en al menos dos dimensiones son LO ESPEJO, EL BOSQUE, CONCHALI, LA PINTANA, SAN RAMON, LA GRANJA, CERRO NAVIA.

## Graficos generados
- `outputs/figures/areas_verdes_m2_hab_bottom10.png`
- `outputs/figures/pobreza_ingresos_top10.png`
- `outputs/figures/ipp_pesos_hab_bottom10.png`
- `outputs/figures/pobreza_vs_areas_verdes_scatter.png`
- `outputs/figures/indice_rezago_territorial_top10.png`
- `pobreza_vs_areas_verdes_scatter.png` se regenero con escala logaritmica en el eje X y una advertencia explicita sobre QUILICURA.

## Outputs tabulares
- `outputs/tablas_hallazgos_fase9.csv`
- `outputs/ranking_areas_verdes.csv`
- `outputs/ranking_pobreza.csv`
- `outputs/ranking_ipp.csv`
- `outputs/indice_rezago_territorial.csv`
