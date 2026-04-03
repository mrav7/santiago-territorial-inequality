# Evaluacion corta Fase 9

## Estado del contexto
- Rama observada en la revision: `main`.
- El repo no esta limpio al momento de esta evaluacion: hay cambios locales de Fase 9 aun no comprometidos.
- Los insumos y outputs de Fase 9 estan presentes: dataset final, SQLite, rankings, indice auxiliar, tablas de hallazgos y cinco graficos exportados.

## Coherencia analitica
- Los rankings de areas verdes, pobreza e IPP coinciden exactamente con el orden derivado desde `data/processed/desigualdad_comunal_final.csv`.
- El indice auxiliar `indice_rezago_territorial` es coherente con los quintiles exportados y con el conteo de `dimensiones_rezago_critico`.
- Las comunas reportadas como rezagadas en dos o mas dimensiones quedan respaldadas por el indice y por `outputs/tablas_hallazgos_fase9.csv`.
- CSV y SQLite siguen alineados en lo esencial para el analisis: mismas 32 filas, misma cobertura de `codigo_comuna` y sin diferencias observadas en pobreza, areas verdes por habitante ni IPP por habitante.

## Outliers y casos a advertir
- `areas_verdes_m2_hab`: QUILICURA (`3931.614773`) aparece como outlier extremo y muy dominante frente a LA REINA (`21.734172`) y PROVIDENCIA (`20.172865`).
  Clasificacion: plausible pero conviene advertirlo.
  Observacion: no hay evidencia aqui de que sea error, pero domina fuertemente la escala y debe mencionarse como caso especial en el informe.
- `areas_verdes_m2_hab`: PROVIDENCIA y LA REINA tambien quedan sobre el umbral IQR, aunque muy lejos de QUILICURA.
  Clasificacion: plausible y comunicable.
- `pobreza_ingresos_pct`: no se detectan outliers por IQR.
  Clasificacion: plausible y comunicable.
- `ipp_pesos_hab`: LO BARNECHEA, VITACURA, LAS CONDES y PROVIDENCIA quedan como outliers altos.
  Clasificacion: plausible y comunicable.
  Observacion: reflejan alta dispersion y conviene explicitar que corresponden a los valores mas altos de capacidad municipal relativa observada.

## Revision visual
- `areas_verdes_m2_hab_bottom10.png`: comunica bien; orden correcto y lectura clara.
- `pobreza_ingresos_top10.png`: comunica bien; orden correcto y lectura clara.
- `ipp_pesos_hab_bottom10.png`: comunica bien; orden correcto y lectura clara.
- `indice_rezago_territorial_top10.png`: comunica bien como ranking auxiliar; conviene recordar en el informe que es una construccion analitica y no una variable oficial de fuente.
- `pobreza_vs_areas_verdes_scatter.png`: util como evidencia exploratoria, pero la escala queda fuertemente comprimida por el valor extremo de QUILICURA y varias etiquetas se superponen cerca del origen.
  Recomendacion: antes del informe, agregar una nota metodologica o un grafico complementario con zoom/tratamiento visual del outlier.

## Recomendacion
- Fase 9 es utilizable y analiticamente coherente.
- Antes de Fase 10 conviene hacer ajustes menores de comunicacion:
  - advertir explicitamente el caso de QUILICURA en areas verdes por habitante;
  - aclarar que el indice de rezago es auxiliar;
  - considerar una mejora menor del scatter para evitar una lectura engañosa por escala extrema.
