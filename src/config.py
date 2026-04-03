from __future__ import annotations

from pathlib import Path

# Raiz del repositorio
BASE_DIR = Path(__file__).resolve().parent.parent
REPOSITORY_NAME = BASE_DIR.name

# Identidad del proyecto
PROJECT_NAME = REPOSITORY_NAME
PROJECT_TITLE = (
    "Desigualdad territorial en Santiago: areas verdes, pobreza por ingresos "
    "y capacidad municipal por comuna"
)
COURSE_NAME = "Inteligencia de Negocios"
LAB_NAME = "Lab 1 - Proceso ETL"
PROJECT_PHASE = "Fase 8"

# Alcance definido
UNIDAD_ANALISIS = "Una fila = una comuna"
COBERTURA_TERRITORIAL = "Provincia de Santiago"
TIPO_ANALISIS = "Comparativo y descriptivo, no causal"

# Carpetas principales
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
STAGING_DIR = DATA_DIR / "staging"
PROCESSED_DIR = DATA_DIR / "processed"
DB_DIR = BASE_DIR / "db"
DOCS_DIR = BASE_DIR / "docs"
DOCS_INFORME_DIR = DOCS_DIR / "informe"
DOCS_PRESENTACION_DIR = DOCS_DIR / "presentacion"
NOTEBOOKS_DIR = BASE_DIR / "notebooks"
OUTPUTS_DIR = BASE_DIR / "outputs"
SRC_DIR = BASE_DIR / "src"

REQUIRED_DIRS = (
    DATA_DIR,
    RAW_DIR,
    STAGING_DIR,
    PROCESSED_DIR,
    DB_DIR,
    DOCS_DIR,
    DOCS_INFORME_DIR,
    DOCS_PRESENTACION_DIR,
    NOTEBOOKS_DIR,
    OUTPUTS_DIR,
    SRC_DIR,
)

# Archivos clave
README_PATH = BASE_DIR / "README.md"
REQUIREMENTS_PATH = BASE_DIR / "requirements.txt"
METADATA_PATH = RAW_DIR / "metadata_fuentes.csv"
DIM_COMUNA_BASE_PATH = RAW_DIR / "dim_comuna_base.csv"

# Ruta estable para la carga final a SQLite en Fase 8.
SQLITE_PATH = DB_DIR / "lab1_desigualdad.sqlite"
PERFILADO_FUENTES_PATH = OUTPUTS_DIR / "perfilado_fuentes.xlsx"
CONFLICTOS_FUENTES_PATH = OUTPUTS_DIR / "conflictos_fuentes.md"
HOMOLOGACION_COMUNAS_PATH = OUTPUTS_DIR / "homologacion_comunas.csv"
RESUMEN_HOMOLOGACION_PATH = OUTPUTS_DIR / "resumen_homologacion.md"
RESUMEN_TRANSFORMACIONES_PATH = OUTPUTS_DIR / "resumen_transformaciones.md"
VALIDACION_STAGING_PATH = OUTPUTS_DIR / "validacion_staging.csv"
FINAL_DATASET_PATH = PROCESSED_DIR / "desigualdad_comunal_final.csv"
LOG_INTEGRACION_PATH = OUTPUTS_DIR / "log_integracion.md"
RESUMEN_DATASET_FINAL_PATH = OUTPUTS_DIR / "resumen_dataset_final.md"
REPORTE_VALIDACION_FINAL_CSV_PATH = OUTPUTS_DIR / "reporte_validacion_final.csv"
REPORTE_VALIDACION_FINAL_MD_PATH = OUTPUTS_DIR / "reporte_validacion_final.md"
REPORTE_CARGA_SQLITE_MD_PATH = OUTPUTS_DIR / "reporte_carga_sqlite.md"
REPORTE_CONSULTAS_SQLITE_CSV_PATH = OUTPUTS_DIR / "reporte_consultas_sqlite.csv"

EXPECTED_DIM_COMUNA_ROWS = 32
EXPECTED_PROVINCIA = "SANTIAGO"
EXPECTED_REGION = "METROPOLITANA DE SANTIAGO"

# Fuentes raw versionadas
FUENTE_A_FILENAME = "datos_municipales_20260402222841_Sin-Corrección-Monetaria.xls"
FUENTE_B_FILENAME = "datos_municipales_20260402223904_Sin-Corrección-Monetaria.xls"
FUENTE_C_FILENAME = "estimaciones_tasa_pobreza_ingresos_comunas_2022.xlsx"
FUENTE_D_FILENAME = "D1_Poblacion-censada-por-sexo-y-edad-en-grupos-quinquenales.xlsx"

FUENTE_A_PATH = RAW_DIR / FUENTE_A_FILENAME
FUENTE_B_PATH = RAW_DIR / FUENTE_B_FILENAME
FUENTE_C_PATH = RAW_DIR / FUENTE_C_FILENAME
FUENTE_D_PATH = RAW_DIR / FUENTE_D_FILENAME

RAW_SOURCES = {
    "A": {
        "nombre_fuente": "SINIM - Areas Verdes",
        "path": FUENTE_A_PATH,
        "archivo_origen": f"data/raw/{FUENTE_A_FILENAME}",
        "archivo_logico": "sinim_areas_verdes_2024_rm.xls",
        "hoja": "Hoja1",
        "skiprows": 2,
        "estrategia_lectura": (
            "SpreadsheetML/XML 2003; no usar pandas.read_excel() directo. "
            "Leer Hoja1 y tratar las dos primeras filas como encabezado previo."
        ),
    },
    "B": {
        "nombre_fuente": "SINIM - Capacidad Municipal",
        "path": FUENTE_B_PATH,
        "archivo_origen": f"data/raw/{FUENTE_B_FILENAME}",
        "archivo_logico": "sinim_capacidad_municipal_ipp_2024_rm.xls",
        "hoja": "Hoja1",
        "skiprows": 2,
        "estrategia_lectura": (
            "SpreadsheetML/XML 2003; no usar pandas.read_excel() directo. "
            "Leer Hoja1 y tratar las dos primeras filas como encabezado previo."
        ),
    },
    "C": {
        "nombre_fuente": "Observatorio Social - Pobreza por Ingresos",
        "path": FUENTE_C_PATH,
        "archivo_origen": f"data/raw/{FUENTE_C_FILENAME}",
        "archivo_logico": "observatorio_social_pobreza_ingresos_2022.xlsx",
        "hoja": "Estimaciones",
        "skiprows": 2,
        "estrategia_lectura": "Excel OOXML; lectura directa con pandas.read_excel().",
    },
    "D": {
        "nombre_fuente": "Censo 2024 - Poblacion Comunal",
        "path": FUENTE_D_PATH,
        "archivo_origen": f"data/raw/{FUENTE_D_FILENAME}",
        "archivo_logico": "ine_poblacion_comunal_2024.xlsx",
        "hoja": "2",
        "skiprows": 3,
        "estrategia_lectura": "Excel OOXML; lectura directa con pandas.read_excel().",
    },
}

STAGING_SOURCE_PATHS = {
    "A": STAGING_DIR / "areas_verdes_staging.csv",
    "B": STAGING_DIR / "ingresos_staging.csv",
    "C": STAGING_DIR / "pobreza_staging.csv",
    "D": STAGING_DIR / "poblacion_staging.csv",
}

FUENTES = {
    source_id: source_data["nombre_fuente"]
    for source_id, source_data in RAW_SOURCES.items()
}

SOURCE_COMUNA_KEY_COLUMNS = {
    "A": {
        "codigo": "codigo_comuna",
        "nombre": "nombre_comuna",
    },
    "B": {
        "codigo": "codigo_comuna",
        "nombre": "nombre_comuna",
    },
    "C": {
        "codigo": "Código",
        "nombre": "Nombre comuna",
    },
    "D": {
        "codigo": "Código comuna",
        "nombre": "Comuna",
    },
}

# La Fase 3 soporta homologaciones manuales futuras, pero con las fuentes
# actuales del proyecto no son necesarias.
COMUNA_HOMOLOGACION_MANUAL: dict[str, str] = {}

METADATA_REQUIRED_COLUMNS = (
    "id_fuente",
    "nombre_fuente",
    "institucion",
    "url",
    "fecha_descarga",
    "formato",
    "anio_referencia",
    "variable_principal",
    "archivo_origen",
    "archivo_logico",
    "hoja",
    "skiprows",
    "observaciones",
)

DIM_COMUNA_BASE_REQUIRED_COLUMNS = (
    "codigo_comuna",
    "nombre_comuna",
    "provincia",
    "region",
    "fuente_referencia",
)

KEY_PATHS = (
    README_PATH,
    REQUIREMENTS_PATH,
    METADATA_PATH,
    DIM_COMUNA_BASE_PATH,
    FUENTE_A_PATH,
    FUENTE_B_PATH,
    FUENTE_C_PATH,
    FUENTE_D_PATH,
)


def ensure_directories() -> None:
    """Crea la estructura minima del proyecto si no existe."""
    for path in REQUIRED_DIRS:
        path.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    ensure_directories()
    print(f"Proyecto: {PROJECT_NAME}")
    print(f"Repositorio: {REPOSITORY_NAME}")
    print(f"Metadata: {METADATA_PATH}")
