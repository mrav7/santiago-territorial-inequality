# lab1-bi-1s2026

Repositorio del **Lab 1 - Proceso ETL** del curso **Inteligencia de Negocios**.

## Tema y alcance

- Tema: desigualdad territorial en Santiago: areas verdes, pobreza por ingresos y capacidad municipal por comuna.
- Unidad de analisis final: una fila = una comuna.
- Cobertura final: Provincia de Santiago.
- Tipo de analisis: comparativo y descriptivo, no causal.

## Estado real del proyecto

El repositorio esta en **Fase 5**. Actualmente `src/main.py` ejecuta de forma reproducible:

1. preflight de estructura y consistencia heredado de Fase 1;
2. Fase 2: lectura real de las 4 fuentes y perfilado diagnostico;
3. Fase 3: validacion de la base maestra comunal y homologacion de nombres por fuente.
4. Fase 4: extraccion reproducible a `staging` por fuente.
5. Fase 5: transformacion de tablas staging por fuente, filtradas al universo final de 32 comunas.

Todavia **no** se implementa el ETL completo. El proyecto no integra aun el dataset final ni genera SQLite.

## Ejecucion

Desde la raiz del repositorio:

```bash
python src/main.py
```

Si todo pasa, el comando regenera estos outputs:

- `outputs/perfilado_fuentes.xlsx`
- `outputs/conflictos_fuentes.md`
- `outputs/homologacion_comunas.csv`
- `outputs/resumen_homologacion.md`
- `outputs/resumen_transformaciones.md`
- `outputs/validacion_staging.csv`

Y deja materializados estos archivos staging:

- `data/staging/areas_verdes_staging.csv`
- `data/staging/ingresos_staging.csv`
- `data/staging/pobreza_staging.csv`
- `data/staging/poblacion_staging.csv`

## Fuentes contempladas

| ID | Fuente | Archivo real |
| --- | --- | --- |
| A | SINIM - Areas Verdes | `data/raw/datos_municipales_20260402222841_Sin-Corrección-Monetaria.xls` |
| B | SINIM - Capacidad Municipal | `data/raw/datos_municipales_20260402223904_Sin-Corrección-Monetaria.xls` |
| C | Observatorio Social - Pobreza por Ingresos | `data/raw/estimaciones_tasa_pobreza_ingresos_comunas_2022.xlsx` |
| D | Censo 2024 - Poblacion Comunal | `data/raw/D1_Poblacion-censada-por-sexo-y-edad-en-grupos-quinquenales.xlsx` |

`data/raw/metadata_fuentes.csv` es el contrato operativo de lectura.

## Estrategia tecnica vigente

### Fase 2

- A y B se leen con parser propio para **SpreadsheetML/XML 2003**; no se tratan como Excel binario clasico.
- C y D se leen con `pandas.read_excel()` respetando `hoja` y `skiprows` definidos en metadata.

### Fase 3

- `data/raw/dim_comuna_base.csv` es la dimension maestra del universo final de 32 comunas.
- La llave principal del proyecto es `codigo_comuna`.
- `nombre_comuna` se usa solo como apoyo descriptivo y de verificacion.
- Los merges futuros no deben hacerse por nombre crudo.

### Fase 4

- Cada fuente se relee desde `data/raw/` usando el contrato de `metadata_fuentes.csv`.
- La salida de Fase 4 se materializa en `data/staging/` con trazabilidad explicita entre archivo raw y archivo staging.

### Fase 5

- Cada fuente se transforma por separado y se filtra al universo final usando `codigo_comuna`.
- Las tablas staging quedan listas para merge futuro, pero aun no se integran entre si.
- Reglas clave:
  - A: el total de areas verdes se construye como parques + plazas.
  - B: el IPP se conserva en miles de pesos nominales 2024.
  - C: la pobreza se convierte desde proporcion 0-1 a porcentaje 0-100.
  - D: se excluyen filas agregadas/notas al filtrar por `codigo_comuna`.

## Estructura relevante del repositorio

```text
lab1-bi-1s2026/
├── data/
│   ├── raw/
│   ├── staging/
│   └── processed/
├── outputs/
├── src/
│   ├── comunas.py
│   ├── config.py
│   ├── extract.py
│   └── main.py
├── README.md
└── requirements.txt
```

## Archivos clave

- `data/raw/metadata_fuentes.csv`: contrato operativo de lectura de las fuentes A-D.
- `data/raw/dim_comuna_base.csv`: universo final maestro de comunas.
- `src/extract.py`: lectura y perfilado de Fase 2.
- `src/comunas.py`: normalizacion comunal, validacion maestra y homologacion de Fase 3.
- `src/transform.py`: exportacion a `staging` y transformaciones por fuente.
- `src/validate.py`: validaciones de staging y documentacion de transformaciones.
- `src/main.py`: orquestacion reproducible del estado actual del proyecto.

## Proximo paso tecnico

Integrar las cuatro tablas limpias en un dataset comunal final y cargarlo a SQLite, manteniendo `codigo_comuna` como llave maestra estable.
