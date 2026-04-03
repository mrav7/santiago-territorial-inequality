# lab1-bi-1s2026

Repositorio del **Lab 1 - Proceso ETL** del curso **Inteligencia de Negocios**.

## Tema y alcance

- Tema: desigualdad territorial en Santiago: areas verdes, pobreza por ingresos y capacidad municipal por comuna.
- Unidad de analisis: una fila = una comuna.
- Cobertura: Provincia de Santiago.
- Tipo de analisis: comparativo y descriptivo, no causal.

## Estado real del proyecto

El repositorio esta en **Fase 1**. Actualmente contiene:

- las 4 fuentes raw reales A-D versionadas en `data/raw/`;
- `data/raw/dim_comuna_base.csv` como dimension base de comunas;
- `data/raw/metadata_fuentes.csv` alineado con los archivos reales;
- un preflight minimo en `src/main.py` para validar estructura y consistencia.

Todavia **no** se implementa el ETL completo. `src/main.py` no genera staging, dataset final ni SQLite; solo verifica que la base de Fase 1 este consistente y lista para auditoria o para iniciar Fase 2.

## Ejecucion

Desde la raiz del repositorio:

```bash
python src/main.py
```

Si todas las validaciones pasan, el script informa que la base de Fase 1 fue verificada. Si encuentra inconsistencias, termina con error y detalla los problemas detectados.

## Fuentes contempladas

| ID | Fuente | Archivo real |
| --- | --- | --- |
| A | SINIM - Areas Verdes | `data/raw/datos_municipales_20260402222841_Sin-Corrección-Monetaria.xls` |
| B | SINIM - Capacidad Municipal | `data/raw/datos_municipales_20260402223904_Sin-Corrección-Monetaria.xls` |
| C | Observatorio Social - Pobreza por Ingresos | `data/raw/estimaciones_tasa_pobreza_ingresos_comunas_2022.xlsx` |
| D | Censo 2024 - Poblacion Comunal | `data/raw/D1_Poblacion-censada-por-sexo-y-edad-en-grupos-quinquenales.xlsx` |

Los metadatos operativos de estas fuentes se registran en `data/raw/metadata_fuentes.csv`, incluyendo `archivo_origen`, `archivo_logico`, `hoja` y `skiprows`.

## Estrategia tecnica de lectura

### Fuentes A y B (SINIM)

Los archivos SINIM con extension `.xls` **no** son libros Excel binarios clasicos. Fueron validados como **SpreadsheetML/XML 2003** con hoja `Hoja1`.

Implicancias para Fase 2:

- no asumir lectura directa con `pandas.read_excel()`;
- parsear el XML de Excel 2003 o convertirlo previamente a una estructura tabular;
- considerar `skiprows=2`, porque las dos primeras filas son encabezado descriptivo y la tercera contiene el encabezado tabular util.

### Fuentes C y D

- Fuente C: lectura directa con `pandas.read_excel(sheet_name="Estimaciones", skiprows=2)`.
- Fuente D: lectura directa con `pandas.read_excel(sheet_name="2", skiprows=3)`.

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

## Archivos clave de Fase 1

- `data/raw/metadata_fuentes.csv`: catalogo operativo de las fuentes A-D.
- `data/raw/dim_comuna_base.csv`: comunas objetivo para el alcance Provincia de Santiago.
- `src/config.py`: rutas y constantes centrales del proyecto.
- `src/main.py`: preflight de Fase 1.

## Proximo paso tecnico

Implementar la Fase 2 sobre esta base validada: extraccion reproducible, normalizacion comunal, staging y dataset integrado final.
- `data/staging/`: archivos intermedios y datasets parcialmente procesados.
- `data/processed/`: dataset final limpio listo para análisis o entrega.
- `db/`: base SQLite del proyecto.
- `src/`: código fuente del pipeline ETL.
- `docs/informe/`: borradores y materiales del informe técnico.
- `docs/presentacion/`: borradores y materiales de la presentación.
- `notebooks/`: análisis exploratorio y pruebas auxiliares.
- `outputs/`: resultados de perfilado, validación, logs y gráficos.

---

## 14. Flujo general del pipeline

El flujo esperado del pipeline es el siguiente:

```python
extract_all_sources()
profile_all_sources()
build_dim_comuna()
transform_green_areas()
transform_municipal_income()
transform_poverty()
transform_population()
integrate_sources()
create_derived_metrics()
validate_final_dataset()
load_csv()
load_sqlite()
export_analysis_outputs()
```

Este orden busca asegurar trazabilidad, limpieza progresiva, validación de calidad y carga reproducible.

---

## 15. Ejecución del proyecto

### 1. Crear y activar entorno virtual

En Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

En Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Ejecutar el pipeline

```bash
python src/main.py
```

> Este comando debe dejar generados los archivos intermedios, el dataset final y la base SQLite.

---

## 16. Archivos clave

- `src/config.py`: rutas, constantes y parámetros globales del proyecto.
- `src/extract.py`: lectura de archivos fuente.
- `src/transform.py`: limpieza, homologación y transformación.
- `src/validate.py`: reglas de validación del dataset final.
- `src/load.py`: exportación a CSV y carga a SQLite.
- `src/main.py`: orquestación completa del pipeline.

---

## 17. Criterios de calidad y validación

El dataset final debe cumplir, al menos, con estas validaciones:

- una sola fila por comuna;
- `codigo_comuna` no nulo;
- población mayor que cero;
- pobreza en rango válido;
- áreas verdes no negativas;
- IPP no negativo;
- ausencia de duplicados comunales;
- métricas derivadas sin infinitos;
- reporte final de nulos por columna.

---

## 18. Limitaciones del proyecto

Este trabajo tiene algunas limitaciones metodológicas que deben ser reconocidas desde el inicio:

- las fuentes no necesariamente comparten el mismo año de referencia;
- el análisis es descriptivo y comparativo;
- no se infiere causalidad;
- la calidad del resultado final depende de la consistencia y disponibilidad de las fuentes públicas.

---

## 19. Estado del proyecto

**Fase actual:** Preparación del proyecto  
**Estado:** En desarrollo

### Próximos hitos

- completar descarga y registro de metadatos de fuentes;
- construir tabla maestra de comunas;
- perfilar cada fuente;
- implementar extracción reproducible;
- iniciar transformaciones por fuente.

---

## 20. Referencias académicas y técnicas

### Documentos base del curso
- Programa del curso Inteligencia de Negocios ICI6442.
- Pauta oficial del Laboratorio I — Proceso ETL.
- Material de clases sobre BI, arquitectura, ETL, Data Warehouse y calidad de datos.

### Bibliografía del curso
- Joyanes Aguilar, L. (2019). *Inteligencia de negocios y analítica de datos: Una visión global de Business Intelligence & Analytics*.
- Sherman, R. (2014). *Business Intelligence Guidebook: From Data Integration to Analytics*.
- Conesa Caralt, J. (Coord.), & Curto Díaz, J. (2010). *Introducción al Business Intelligence*.

---

## 21. Observaciones finales

Este repositorio no solo busca cumplir con una evaluación académica, sino también reflejar buenas prácticas de trabajo en proyectos de datos: trazabilidad, reproducibilidad, claridad metodológica, separación por etapas y documentación suficiente para defensa técnica y presentación oral. La meta no es únicamente “hacer correr código”, sino demostrar comprensión del proceso ETL y su valor dentro de una arquitectura de Inteligencia de Negocios.
