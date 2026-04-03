# lab1-bi-1s2026

Repositorio del **Lab 1 — Proceso ETL** del curso **Inteligencia de Negocios**.

## Tema y alcance

- **Tema:** desigualdad territorial en Santiago: áreas verdes, pobreza por ingresos y capacidad municipal por comuna.
- **Unidad de análisis:** una fila = una comuna.
- **Cobertura objetivo:** Provincia de Santiago.
- **Tipo de análisis:** comparativo y descriptivo, no causal.

## Estado actual del proyecto

El repositorio se encuentra en **Fase 2: perfilado y diagnóstico de fuentes**.

Actualmente contiene:

- las 4 fuentes raw reales A–D versionadas en `data/raw/`;
- `data/raw/dim_comuna_base.csv` como base oficial de comunas objetivo;
- `data/raw/metadata_fuentes.csv` como contrato operativo de lectura;
- un flujo reproducible desde `src/main.py` que ejecuta:
  - preflight heredado de Fase 1;
  - lectura real de las 4 fuentes;
  - perfilado por fuente;
  - exportación de evidencia diagnóstica a `outputs/`.

### Qué sí hace hoy el repositorio

- valida la estructura mínima del proyecto;
- relee las 4 fuentes reales;
- usa `metadata_fuentes.csv` para parámetros operativos de lectura;
- resuelve la lectura especial de A/B en formato SpreadsheetML/XML 2003;
- genera outputs diagnósticos reproducibles.

### Qué todavía no hace

Todavía **no** está implementado el ETL completo.  
En el estado actual, `src/main.py` **no**:

- construye el dataset final integrado;
- genera archivos en `data/processed/` como salida final del laboratorio;
- carga resultados a SQLite.

Eso corresponde a fases posteriores del proyecto.

## Ejecución actual

Desde la raíz del repositorio:

```bash
python src/main.py
```

Si todas las validaciones pasan, el script:

1. verifica la base de Fase 1;
2. ejecuta la Fase 2;
3. genera o actualiza:

- `outputs/perfilado_fuentes.xlsx`
- `outputs/conflictos_fuentes.md`

Si encuentra inconsistencias, termina con error y reporta los problemas detectados.

## Fuentes contempladas

| ID | Fuente | Archivo real |
| --- | --- | --- |
| A | SINIM - Áreas Verdes | `data/raw/datos_municipales_20260402222841_Sin-Corrección-Monetaria.xls` |
| B | SINIM - Capacidad Municipal | `data/raw/datos_municipales_20260402223904_Sin-Corrección-Monetaria.xls` |
| C | Observatorio Social - Pobreza por Ingresos | `data/raw/estimaciones_tasa_pobreza_ingresos_comunas_2022.xlsx` |
| D | Censo 2024 - Población Comunal | `data/raw/D1_Poblacion-censada-por-sexo-y-edad-en-grupos-quinquenales.xlsx` |

Los metadatos operativos de estas fuentes se registran en `data/raw/metadata_fuentes.csv`, incluyendo:

- `archivo_origen`
- `archivo_logico`
- `hoja`
- `skiprows`
- observaciones técnicas relevantes

## Estrategia técnica de lectura

### Fuentes A y B (SINIM)

Los archivos SINIM con extensión `.xls` **no** corresponden a libros Excel binarios clásicos.  
Se validaron como **SpreadsheetML/XML 2003** con hoja `Hoja1`.

Implicancias:

- no asumir lectura directa con `pandas.read_excel()` como si fueran `.xls` tradicionales;
- usar parser específico para SpreadsheetML/XML 2003;
- considerar `skiprows=2`, ya que las primeras filas contienen encabezado descriptivo previo al encabezado tabular útil.

### Fuentes C y D

Estas fuentes sí se leen con `pandas.read_excel()` usando la metadata operativa:

- **Fuente C:** `sheet_name="Estimaciones"`, `skiprows=2`
- **Fuente D:** `sheet_name="2"`, `skiprows=3`

## Outputs actuales de Fase 2

### `outputs/perfilado_fuentes.xlsx`
Incluye perfilado reproducible por fuente, con información como:

- nombre de archivo;
- número de filas y columnas;
- nombres de columnas;
- tipos de datos;
- nulos;
- duplicados;
- muestras de texto;
- parser utilizado.

### `outputs/conflictos_fuentes.md`
Resume conflictos detectados para fases posteriores, entre ellos:

- diferencias de nombres de comuna;
- prioridad de `codigo_comuna` sobre `nombre_comuna`;
- celdas especiales no numéricas;
- filas de notas, totales o blancos;
- diferencia entre cobertura de la fuente y cobertura final del proyecto.

## Estructura del repositorio

```text
lab1-bi-1s2026/
├── data/
│   ├── raw/
│   ├── staging/
│   └── processed/
├── db/
├── docs/
│   ├── informe/
│   └── presentacion/
├── notebooks/
├── outputs/
├── src/
│   ├── config.py
│   ├── extract.py
│   ├── load.py
│   ├── main.py
│   ├── transform.py
│   └── validate.py
├── .gitignore
├── README.md
└── requirements.txt
```

## Archivos clave actuales

- `data/raw/metadata_fuentes.csv`: contrato operativo de lectura de fuentes.
- `data/raw/dim_comuna_base.csv`: base comunal oficial del proyecto.
- `src/config.py`: rutas y constantes centrales.
- `src/extract.py`: lectura reproducible y perfilado por fuente.
- `src/main.py`: preflight + ejecución de Fase 2.
- `outputs/perfilado_fuentes.xlsx`: evidencia de perfilado.
- `outputs/conflictos_fuentes.md`: evidencia de diagnóstico.

## Próximo paso técnico

El siguiente paso es **Fase 3: estandarización de la llave maestra comunal**, seguida por la transformación por fuente.

Eso implica:

- consolidar `codigo_comuna` como llave principal;
- homologar nombres de comuna;
- filtrar todas las fuentes al universo final de 32 comunas;
- preparar tablas limpias en `data/staging/` para integración posterior.

## Entorno recomendado

### Crear y activar entorno virtual

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
```

### Instalar dependencias

```bash
pip install -r requirements.txt
```

## Notas metodológicas

- no cambiar el universo de comunas a mitad del proyecto;
- no hacer joins por nombre de comuna si existe `codigo_comuna`;
- no mezclar años sin declararlo;
- no presentar resultados como relaciones causales;
- no editar archivos raw manualmente para “limpiarlos”.

## Referencias base

### Documentos del curso
- Programa del curso Inteligencia de Negocios ICI6442.
- Pauta oficial del Laboratorio I — Proceso ETL.
- Material de clases sobre BI, arquitectura, ETL, Data Warehouse y calidad de datos.

### Bibliografía
- Joyanes Aguilar, L. (2019). *Inteligencia de negocios y analítica de datos: Una visión global de Business Intelligence & Analytics*.
- Sherman, R. (2014). *Business Intelligence Guidebook: From Data Integration to Analytics*.
- Conesa Caralt, J. (Coord.), & Curto Díaz, J. (2010). *Introducción al Business Intelligence*.
