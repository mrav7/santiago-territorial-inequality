# Handoff al template externo

Este directorio reúne un paquete espejo de materiales para la Fase 10, preparado dentro del repo ETL y pensado para copiarse luego a `informe-lab1` sin rehacer contenido.

## Qué contiene

- `Resumen.tex`
- `Secciones/01_introduccion.tex` a `Secciones/14_conclusiones.tex`
- `Anexos/anexos.tex`
- `Tablas/*.tex`
- `Figuras/` con manifiesto y copias de las figuras analíticas
- `referencias_lab1.bib`
- `trazabilidad_informe.csv`
- `reporte_preparacion_fase10.md`

## Sugerencia de traspaso

1. Copiar `Resumen.tex`, `Secciones/`, `Anexos/`, `Tablas/`, `Figuras/` y `referencias_lab1.bib` al template manteniendo la estructura relativa.
2. Poblar el archivo de metadatos del template usando `00_metadatos_sugeridos.md`.
3. Incluir `Resumen.tex` y luego las secciones en el orden 01-14.
4. Incluir `Anexos/anexos.tex` al final, después de las referencias.
5. Revisar el archivo `trazabilidad_informe.csv` si se requiere justificar el origen de una afirmación o una cifra.

## Supuestos de ruta

- Las secciones llaman tablas con `\input{Tablas/...}`.
- Las secciones llaman figuras con `\includegraphics{Figuras/...}`.
- Si se preserva esta estructura al copiar, no deberían requerirse cambios de rutas.

## Alcance del paquete

- No modifica el template externo.
- No reescribe Fases 1 a 9.
- No altera `data/raw/`, el pipeline ETL ni la llave `codigo_comuna`.
- No agrega resultados no respaldados por evidencia del repositorio.
