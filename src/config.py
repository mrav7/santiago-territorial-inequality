from pathlib import Path

# Raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# Carpetas principales
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
STAGING_DIR = DATA_DIR / "staging"
PROCESSED_DIR = DATA_DIR / "processed"

DB_DIR = BASE_DIR / "db"
DOCS_DIR = BASE_DIR / "docs"
NOTEBOOKS_DIR = BASE_DIR / "notebooks"
OUTPUTS_DIR = BASE_DIR / "outputs"
SRC_DIR = BASE_DIR / "src"

# Archivos clave
SQLITE_PATH = DB_DIR / "lab1_desigualdad.sqlite"
METADATA_PATH = RAW_DIR / "metadata_fuentes.csv"
DIM_COMUNA_BASE_PATH = RAW_DIR / "dim_comuna_base.csv"

README_PATH = BASE_DIR / "README.md"
REQUIREMENTS_PATH = BASE_DIR / "requirements.txt"

# Configuración del proyecto
PROJECT_NAME = "lab1_desigualdad_territorial"
PROJECT_TITLE = "Desigualdad territorial en Santiago: áreas verdes, pobreza por ingresos y capacidad municipal por comuna"

# Alcance definido
UNIDAD_ANALISIS = "Una fila = una comuna"
COBERTURA_TERRITORIAL = "Provincia de Santiago"
TIPO_ANALISIS = "Comparativo y descriptivo, no causal"

# Fuentes oficiales definidas
FUENTES = {
    "A": "SINIM - Areas Verdes",
    "B": "SINIM - Capacidad Municipal",
    "C": "Observatorio Social - Pobreza por Ingresos",
    "D": "Censo 2024 - Poblacion Comunal",
}

# Nombres sugeridos de archivos staging
STAGING_FILES = {
    "areas_verdes": STAGING_DIR / "areas_verdes_staging.csv",
    "capacidad_municipal": STAGING_DIR / "capacidad_municipal_staging.csv",
    "pobreza_ingresos": STAGING_DIR / "pobreza_ingresos_staging.csv",
    "poblacion": STAGING_DIR / "poblacion_staging.csv",
}

# Dataset final esperado
FINAL_DATASET_PATH = PROCESSED_DIR / "desigualdad_comunal_final.csv"


def ensure_directories() -> None:
    """Crea las carpetas necesarias si no existen."""
    for path in [
        DATA_DIR,
        RAW_DIR,
        STAGING_DIR,
        PROCESSED_DIR,
        DB_DIR,
        DOCS_DIR,
        NOTEBOOKS_DIR,
        OUTPUTS_DIR,
        SRC_DIR,
    ]:
        path.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    ensure_directories()
    print(f"Proyecto: {PROJECT_NAME}")
    print(f"Base dir: {BASE_DIR}")
    print(f"Metadata: {METADATA_PATH}")
    print(f"SQLite: {SQLITE_PATH}")