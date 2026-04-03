# Laboratorio I — Proceso ETL
## Desigualdad territorial en Santiago: áreas verdes, pobreza por ingresos y capacidad municipal por comuna

### Inteligencia de Negocios — ICI6442
**Período:** 1S 2026  
**Profesor:** Ignacio Toro Cabrera  
**Escuela:** Escuela de Informática PUCV  

---

## Integrantes

- Matías Andrade Valenzuela

---

## 1. Descripción del proyecto

Este repositorio contiene el desarrollo del **Laboratorio I de Inteligencia de Negocios (ICI6442)**, centrado en la implementación de un proceso **ETL (Extract, Transform, Load)** completo y reproducible.

El proyecto aborda el problema de la **desigualdad territorial en Santiago**, integrando información comunal proveniente de múltiples fuentes públicas para construir un dataset limpio y estructurado que permita comparar tres dimensiones:

- disponibilidad de áreas verdes;
- pobreza por ingresos;
- capacidad municipal.

Desde la lógica del curso, la Inteligencia de Negocios busca transformar datos en información útil para apoyar la toma de decisiones, y el proceso ETL cumple un rol central en esa transformación al extraer, limpiar, integrar y cargar datos desde múltiples fuentes hacia una estructura final consistente.

---

## 2. Objetivo general

Desarrollar un proceso ETL completo y funcional que integre múltiples fuentes de datos comunales para construir un dataset final orientado al análisis descriptivo de desigualdad territorial en Santiago.

## 3. Objetivos específicos

- Extraer datos desde al menos cuatro fuentes públicas distintas.
- Explorar las fuentes para identificar su estructura, calidad, tipos de atributos y conflictos potenciales.
- Diseñar un modelo de datos y un mapa lógico de datos.
- Aplicar transformaciones de limpieza, normalización, conversión e integración.
- Generar un dataset final limpio por comuna.
- Cargar el resultado final en formato CSV y en una base de datos SQLite.
- Documentar técnica y metodológicamente todo el proceso.

---

## 4. Contexto académico

Este trabajo corresponde al **Laboratorio I** del curso **Inteligencia de Negocios (ICI6442)**. Según el programa del curso, los laboratorios evalúan progresivamente contenidos asociados a ETL, Data Warehouse, KDD, minería de datos y calidad de datos. En particular, el **Laboratorio 1** está enfocado en **Extracción, Transformación y Carga de Datos (ETL)**.

---

## 5. Descripción de la evaluación

De acuerdo con la pauta del laboratorio, este trabajo debe cumplir con los siguientes requerimientos:

- usar al menos **3 fuentes de datos** diferentes;
- explorar estructura, calidad, tipos de atributos y conflictos;
- diseñar un **modelo de datos**;
- elaborar un **mapa lógico de datos**;
- implementar un proceso **ETL completo**;
- aplicar al menos **6 transformaciones**;
- cargar el resultado a una base de datos o a un dataset limpio;
- documentar el proceso en un informe técnico;
- presentar el trabajo oralmente al curso.

### Entregables exigidos

- Informe en PDF  
- Diapositivas en PDF  
- Código fuente del ETL  
- Datos originales o enlaces  
- Dataset final transformado

### Ponderación del laboratorio

- **Presentación oral:** 60%
- **Informe escrito:** 40%

### Requisitos formales relevantes

- grupos de **1 a 2 integrantes**;
- todos los entregables deben estar completos;
- penalización de **10 puntos por hora de retraso**;
- el informe debe seguir el **formato escuela**;
- la entrega final debe comprimirse en archivo `.7zip` con el nombre indicado por la pauta.

### Fechas importantes del laboratorio

- **Entrega:** viernes 10 de abril de 2026, 23:59
- **Presentaciones:** viernes 17 de abril de 2026

---

## 6. Alcance del trabajo

Para este proyecto se fijaron las siguientes decisiones metodológicas:

- **Tema:** Desigualdad territorial en Santiago: áreas verdes, pobreza por ingresos y capacidad municipal por comuna.
- **Unidad de análisis:** una fila representa una comuna.
- **Cobertura territorial:** Provincia de Santiago.
- **Naturaleza del análisis:** comparativo y descriptivo.
- **Corte analítico:** perfil comunal integrado a partir de indicadores recientes disponibles.

Este proyecto no busca establecer relaciones causales, sino construir una base integrada y confiable para comparar comunas bajo tres dimensiones relevantes.

---

## 7. Pregunta del proyecto

**¿Cómo se expresa la desigualdad territorial entre comunas de Santiago al integrar indicadores de áreas verdes, pobreza por ingresos y capacidad municipal?**

### Preguntas de apoyo

- ¿Qué comunas presentan menos áreas verdes por habitante?
- ¿Qué comunas combinan alta pobreza y baja disponibilidad relativa de áreas verdes?
- ¿Qué diferencias se observan entre comunas con mayor y menor capacidad municipal?
- ¿Qué comunas aparecen más rezagadas al combinar las tres dimensiones?

---

## 8. Fuentes de datos

El proyecto trabaja con **cuatro fuentes públicas**, superando el mínimo exigido por la pauta:

### Fuente A — SINIM: áreas verdes
Uso principal: medir superficie de áreas verdes con mantenimiento y, de manera complementaria, número de parques y plazas.

### Fuente B — SINIM: capacidad municipal
Uso principal: medir capacidad financiera local mediante indicadores como ingresos propios permanentes (IPP) e ingresos municipales totales.

### Fuente C — Observatorio Social: pobreza por ingresos comunal
Uso principal: medir vulnerabilidad socioeconómica mediante la tasa de pobreza por ingresos.

### Fuente D — Censo 2024: población comunal
Uso principal: obtener la población comunal para construir indicadores relativos y per cápita.

> Las URLs exactas, fechas de descarga, formatos y observaciones de cada fuente deben quedar registradas en el archivo de metadatos del proyecto.

---

## 9. Descripción del trabajo realizado

El trabajo consiste en construir un pipeline ETL reproducible en Python que permita:

1. **Extraer** los datos desde fuentes heterogéneas.
2. **Perfilar** cada fuente para detectar problemas de calidad.
3. **Estandarizar** nombres y códigos de comuna.
4. **Transformar** los datos mediante reglas de limpieza y normalización.
5. **Integrar** todas las fuentes en una tabla comunal única.
6. **Derivar** indicadores comparables, como:
   - áreas verdes por habitante;
   - IPP por habitante.
7. **Validar** la calidad del resultado final.
8. **Cargar** el dataset final en CSV y SQLite.

En términos conceptuales, el pipeline sigue la arquitectura tradicional de BI estudiada en el curso: capa de fuentes, integración ETL, almacenamiento de datos y soporte posterior al análisis y la visualización.

---

## 10. Transformaciones esperadas

Como parte del laboratorio, el proceso contempla al menos las siguientes transformaciones documentadas:

- selección de columnas relevantes;
- renombrado estandarizado de columnas;
- normalización de nombres de comuna;
- homologación de código de comuna;
- conversión de tipos de datos;
- limpieza de nulos o valores inválidos;
- eliminación de duplicados;
- filtrado territorial;
- estandarización de unidades monetarias;
- validación de rangos;
- creación de métricas derivadas.

---

## 11. Producto final esperado

El resultado del proyecto corresponde a:

- un **dataset final limpio** con una fila por comuna;
- una base de datos **SQLite** con tablas estructuradas;
- salidas auxiliares para validación, perfilado y análisis;
- insumos para informe técnico y presentación oral.

### Estructura general del dataset final

Columnas mínimas esperadas:

- `codigo_comuna`
- `nombre_comuna`
- `poblacion`
- `anio_poblacion`
- `pobreza_ingresos_pct`
- `anio_pobreza`
- `areas_verdes_m2`
- `anio_areas_verdes`
- `ipp_miles_pesos`
- `anio_ingresos`
- `areas_verdes_m2_hab`
- `ipp_pesos_hab`

### Tablas esperadas en SQLite

- `dim_comuna`
- `fact_desigualdad_comunal`
- `metadata_fuentes`

---

## 12. Stack tecnológico

El entorno técnico recomendado para este proyecto es:

- **Python 3.11**
- **pandas**
- **openpyxl**
- **numpy**
- **matplotlib**
- **sqlite3**
- **pathlib**
- **re**
- **unicodedata**
- **Jupyter Notebook** para exploración auxiliar

La convención técnica del proyecto establece que todo el pipeline debe ser reproducible desde `main.py`, sin trabajar directamente sobre los archivos en `raw/`, dejando resultados intermedios en `staging/` y resultados finales en `processed/` y SQLite.

---

## 13. Estructura del repositorio

```text
lab1_desigualdad_territorial/
├── data/
│   ├── raw/
│   ├── staging/
│   └── processed/
├── db/
├── src/
│   ├── config.py
│   ├── extract.py
│   ├── transform.py
│   ├── validate.py
│   ├── load.py
│   └── main.py
├── docs/
│   ├── informe/
│   └── presentacion/
├── notebooks/
├── outputs/
├── README.md
├── requirements.txt
└── .gitignore
```

### Descripción de carpetas

- `data/raw/`: archivos originales descargados desde las fuentes.
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
