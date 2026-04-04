from __future__ import annotations

import csv
import math
import shutil
import sqlite3
import subprocess
import textwrap
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook


ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = ROOT / "docs" / "informe_lab1_materiales"
SECCIONES_DIR = DOCS_DIR / "Secciones"
ANEXOS_DIR = DOCS_DIR / "Anexos"
TABLAS_DIR = DOCS_DIR / "Tablas"
FIGURAS_DIR = DOCS_DIR / "Figuras"
VALIDACION_DIR = DOCS_DIR / "_validacion"

DATASET_PATH = ROOT / "data" / "processed" / "desigualdad_comunal_final.csv"
SQLITE_PATH = ROOT / "db" / "lab1_desigualdad.sqlite"
METADATA_PATH = ROOT / "data" / "raw" / "metadata_fuentes.csv"
DIM_COMUNA_BASE_PATH = ROOT / "data" / "raw" / "dim_comuna_base.csv"
HOMOLOGACION_PATH = ROOT / "outputs" / "homologacion_comunas.csv"
VALIDACION_FINAL_CSV_PATH = ROOT / "outputs" / "reporte_validacion_final.csv"
VALIDACION_FINAL_MD_PATH = ROOT / "outputs" / "reporte_validacion_final.md"
VALIDACION_STAGING_PATH = ROOT / "outputs" / "validacion_staging.csv"
PERFILADO_XLSX_PATH = ROOT / "outputs" / "perfilado_fuentes.xlsx"
CONFLICTOS_PATH = ROOT / "outputs" / "conflictos_fuentes.md"
RESUMEN_HOMOLOGACION_PATH = ROOT / "outputs" / "resumen_homologacion.md"
RESUMEN_TRANSFORMACIONES_PATH = ROOT / "outputs" / "resumen_transformaciones.md"
LOG_INTEGRACION_PATH = ROOT / "outputs" / "log_integracion.md"
RESUMEN_DATASET_FINAL_PATH = ROOT / "outputs" / "resumen_dataset_final.md"
REPORTE_CARGA_SQLITE_PATH = ROOT / "outputs" / "reporte_carga_sqlite.md"
REPORTE_CONSULTAS_SQLITE_PATH = ROOT / "outputs" / "reporte_consultas_sqlite.csv"
ANALISIS_PATH = ROOT / "outputs" / "analisis_exploratorio.md"
EVALUACION_CORTA_FASE9_PATH = ROOT / "outputs" / "evaluacion_corta_fase9.md"
REPORTE_CORRECCIONES_PATH = ROOT / "outputs" / "reporte_correcciones_pre_fase10.md"
TABLAS_HALLAZGOS_PATH = ROOT / "outputs" / "tablas_hallazgos_fase9.csv"
RANKING_AREAS_PATH = ROOT / "outputs" / "ranking_areas_verdes.csv"
RANKING_POBREZA_PATH = ROOT / "outputs" / "ranking_pobreza.csv"
RANKING_IPP_PATH = ROOT / "outputs" / "ranking_ipp.csv"
INDICE_REZAGO_PATH = ROOT / "outputs" / "indice_rezago_territorial.csv"
OUTPUTS_FIGURES_DIR = ROOT / "outputs" / "figures"

FIGURE_FILES = [
    "areas_verdes_m2_hab_bottom10.png",
    "pobreza_ingresos_top10.png",
    "ipp_pesos_hab_bottom10.png",
    "pobreza_vs_areas_verdes_scatter.png",
    "indice_rezago_territorial_top10.png",
]

EXPECTED_FINAL_COLUMNS = [
    "codigo_comuna",
    "nombre_comuna",
    "poblacion",
    "anio_poblacion",
    "pobreza_ingresos_pct",
    "anio_pobreza",
    "areas_verdes_m2",
    "anio_areas_verdes",
    "ipp_miles_pesos",
    "anio_ingresos",
    "areas_verdes_m2_hab",
    "ipp_pesos_hab",
]


def relpath(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def ensure_dirs() -> None:
    for path in (DOCS_DIR, SECCIONES_DIR, ANEXOS_DIR, TABLAS_DIR, FIGURAS_DIR, VALIDACION_DIR):
        path.mkdir(parents=True, exist_ok=True)


def escape_latex(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    text = str(value)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def latex_code(text: str) -> str:
    return rf"\texttt{{{escape_latex(text)}}}"


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def read_md(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_csv(path: Path, **kwargs) -> pd.DataFrame:
    return pd.read_csv(path, **kwargs)


def load_perfilado_summary() -> tuple[pd.DataFrame, pd.DataFrame]:
    wb = load_workbook(PERFILADO_XLSX_PATH, data_only=True)
    try:
        resumen_rows = list(wb["resumen"].values)
        columnas_rows = list(wb["columnas"].values)
    finally:
        wb.close()
    resumen = pd.DataFrame(resumen_rows[1:], columns=resumen_rows[0])
    columnas = pd.DataFrame(columnas_rows[1:], columns=columnas_rows[0])
    return resumen, columnas


def format_decimal(value: object, decimals: int = 4) -> str:
    if value is None:
        return "NA"
    if isinstance(value, str):
        return value
    if isinstance(value, float) and math.isnan(value):
        return "NA"
    return f"{float(value):.{decimals}f}"


def format_int(value: object) -> str:
    if value is None:
        return "NA"
    if isinstance(value, float) and math.isnan(value):
        return "NA"
    return f"{int(value)}"


def latex_table(
    *,
    caption: str,
    label: str,
    colspec: str,
    headers: list[str],
    rows: list[list[object]],
    size: str = r"\footnotesize",
) -> str:
    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        size,
        rf"\caption{{{escape_latex(caption)}}}",
        rf"\begin{{tabular}}{{{colspec}}}",
        r"\hline",
        " & ".join(escape_latex(header) for header in headers) + r" \\",
        r"\hline",
    ]
    for row in rows:
        lines.append(" & ".join(escape_latex(cell) for cell in row) + r" \\")
    lines.extend(
        [
            r"\hline",
            r"\end{tabular}",
            r"\end{table}",
        ]
    )
    return "\n".join(lines)


def build_context() -> dict[str, object]:
    dataset = read_csv(DATASET_PATH, dtype={"codigo_comuna": "string"})
    metadata = read_csv(METADATA_PATH, dtype=str).fillna("")
    dim_base = read_csv(DIM_COMUNA_BASE_PATH, dtype={"codigo_comuna": "string"})
    homologacion = read_csv(HOMOLOGACION_PATH, dtype={"codigo_comuna": "string"}).fillna("")
    validacion_final = read_csv(VALIDACION_FINAL_CSV_PATH, dtype=str).fillna("")
    validacion_staging = read_csv(VALIDACION_STAGING_PATH, dtype=str).fillna("")
    consultas_sqlite = read_csv(REPORTE_CONSULTAS_SQLITE_PATH, dtype=str).fillna("")
    hallazgos = read_csv(TABLAS_HALLAZGOS_PATH, dtype={"codigo_comuna": "string"})
    ranking_areas = read_csv(RANKING_AREAS_PATH, dtype={"codigo_comuna": "string"})
    ranking_pobreza = read_csv(RANKING_POBREZA_PATH, dtype={"codigo_comuna": "string"})
    ranking_ipp = read_csv(RANKING_IPP_PATH, dtype={"codigo_comuna": "string"})
    indice_rezago = read_csv(INDICE_REZAGO_PATH, dtype={"codigo_comuna": "string"})
    perfilado_resumen, perfilado_columnas = load_perfilado_summary()

    dataset_rows = len(dataset)
    dataset_cols = len(dataset.columns)
    duplicated_codes = int(dataset["codigo_comuna"].duplicated().sum())
    null_counts = dataset.isna().sum().to_dict()

    sqlite_counts: dict[str, int] = {}
    sqlite_schema: dict[str, list[tuple[object, ...]]] = {}
    with sqlite3.connect(SQLITE_PATH) as connection:
        cursor = connection.cursor()
        table_names = [
            row[0]
            for row in cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).fetchall()
        ]
        quick_check = cursor.execute("PRAGMA quick_check").fetchone()[0]
        for table in ("dim_comuna", "fact_desigualdad_comunal", "metadata_fuentes"):
            sqlite_counts[table] = int(cursor.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
            sqlite_schema[table] = cursor.execute(f"PRAGMA table_info({table})").fetchall()

    homologacion_scope = homologacion[homologacion["nombre_comuna_base"] != ""].copy()
    homologacion_summary = (
        homologacion_scope.groupby(["fuente", "tipo_diferencia"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )
    for column in (
        "coincidencia_exacta",
        "coincidencia_por_normalizacion",
        "coincidencia_por_homologacion_manual",
        "requiere_homologacion_manual",
    ):
        if column not in homologacion_summary.columns:
            homologacion_summary[column] = 0

    top_bottom_areas = hallazgos[hallazgos["tabla"] == "top_5_menor_areas_verdes_m2_hab"].copy()
    top_pobreza = hallazgos[hallazgos["tabla"] == "top_5_mayor_pobreza_ingresos_pct"].copy()
    top_ipp = hallazgos[hallazgos["tabla"] == "top_5_menor_ipp_pesos_hab"].copy()
    peor_pobreza_areas = hallazgos[hallazgos["tabla"] == "peor_quintil_pobreza_y_areas_verdes"].copy()
    peor_pobreza_ipp = hallazgos[hallazgos["tabla"] == "peor_quintil_pobreza_y_ipp"].copy()
    rezagadas_multidim = hallazgos[
        hallazgos["tabla"] == "rezagadas_en_dos_o_mas_dimensiones"
    ].copy()

    quilicura_row = ranking_areas[ranking_areas["nombre_comuna"] == "QUILICURA"].iloc[0]
    la_reina_row = ranking_areas[ranking_areas["nombre_comuna"] == "LA REINA"].iloc[0]
    providencia_row = ranking_areas[ranking_areas["nombre_comuna"] == "PROVIDENCIA"].iloc[0]

    outputs_presence = {
        "outputs/analisis_exploratorio.md": ANALISIS_PATH.exists(),
        "outputs/tablas_hallazgos_fase9.csv": TABLAS_HALLAZGOS_PATH.exists(),
        "outputs/ranking_areas_verdes.csv": RANKING_AREAS_PATH.exists(),
        "outputs/ranking_pobreza.csv": RANKING_POBREZA_PATH.exists(),
        "outputs/ranking_ipp.csv": RANKING_IPP_PATH.exists(),
        "outputs/indice_rezago_territorial.csv": INDICE_REZAGO_PATH.exists(),
        "outputs/reporte_carga_sqlite.md": REPORTE_CARGA_SQLITE_PATH.exists(),
        "outputs/reporte_consultas_sqlite.csv": REPORTE_CONSULTAS_SQLITE_PATH.exists(),
        "outputs/reporte_validacion_final.md": VALIDACION_FINAL_MD_PATH.exists(),
        "outputs/reporte_validacion_final.csv": VALIDACION_FINAL_CSV_PATH.exists(),
        "outputs/log_integracion.md": LOG_INTEGRACION_PATH.exists(),
        "outputs/resumen_transformaciones.md": RESUMEN_TRANSFORMACIONES_PATH.exists(),
        "outputs/conflictos_fuentes.md": CONFLICTOS_PATH.exists(),
        "outputs/perfilado_fuentes.xlsx": PERFILADO_XLSX_PATH.exists(),
    }

    return {
        "dataset": dataset,
        "metadata": metadata,
        "dim_base": dim_base,
        "homologacion": homologacion,
        "homologacion_summary": homologacion_summary,
        "validacion_final": validacion_final,
        "validacion_staging": validacion_staging,
        "consultas_sqlite": consultas_sqlite,
        "hallazgos": hallazgos,
        "ranking_areas": ranking_areas,
        "ranking_pobreza": ranking_pobreza,
        "ranking_ipp": ranking_ipp,
        "indice_rezago": indice_rezago,
        "perfilado_resumen": perfilado_resumen,
        "perfilado_columnas": perfilado_columnas,
        "dataset_rows": dataset_rows,
        "dataset_cols": dataset_cols,
        "duplicated_codes": duplicated_codes,
        "null_counts": null_counts,
        "sqlite_counts": sqlite_counts,
        "sqlite_schema": sqlite_schema,
        "sqlite_tables": table_names,
        "sqlite_quick_check": quick_check,
        "top_bottom_areas": top_bottom_areas,
        "top_pobreza": top_pobreza,
        "top_ipp": top_ipp,
        "peor_pobreza_areas": peor_pobreza_areas,
        "peor_pobreza_ipp": peor_pobreza_ipp,
        "rezagadas_multidim": rezagadas_multidim,
        "quilicura_row": quilicura_row,
        "la_reina_row": la_reina_row,
        "providencia_row": providencia_row,
        "outputs_presence": outputs_presence,
    }


def create_tables(ctx: dict[str, object]) -> None:
    metadata: pd.DataFrame = ctx["metadata"]  # type: ignore[assignment]
    perfilado_resumen: pd.DataFrame = ctx["perfilado_resumen"]  # type: ignore[assignment]
    homologacion_summary: pd.DataFrame = ctx["homologacion_summary"]  # type: ignore[assignment]
    consultas_sqlite: pd.DataFrame = ctx["consultas_sqlite"]  # type: ignore[assignment]
    hallazgos: pd.DataFrame = ctx["hallazgos"]  # type: ignore[assignment]
    validacion_final: pd.DataFrame = ctx["validacion_final"]  # type: ignore[assignment]
    sqlite_schema: dict[str, list[tuple[object, ...]]] = ctx["sqlite_schema"]  # type: ignore[assignment]
    sqlite_counts: dict[str, int] = ctx["sqlite_counts"]  # type: ignore[assignment]
    homologacion: pd.DataFrame = ctx["homologacion"]  # type: ignore[assignment]

    tabla_fuentes_rows = []
    for _, row in metadata.iterrows():
        tabla_fuentes_rows.append(
            [
                row["id_fuente"],
                row["nombre_fuente"],
                row["institucion"],
                row["anio_referencia"],
                row["formato"],
                row["archivo_origen"],
                row["variable_principal"],
            ]
        )
    write_text(
        TABLAS_DIR / "tabla_fuentes.tex",
        latex_table(
            caption="Resumen de fuentes primarias utilizadas en el ETL.",
            label="tab:fuentes",
            colspec="|c|p{3.0cm}|p{2.8cm}|c|p{2.2cm}|p{3.8cm}|p{2.2cm}|",
            headers=["ID", "Fuente", "Institución", "Año", "Formato", "Archivo origen", "Variable principal"],
            rows=tabla_fuentes_rows,
        ),
    )

    tabla_decisiones_rows = [
        ["Unidad de análisis", "Una fila = una comuna", "README.md; outputs/resumen_dataset_final.md"],
        ["Cobertura territorial", "Provincia de Santiago, 32 comunas", "data/raw/dim_comuna_base.csv; outputs/reporte_validacion_final.md"],
        ["Llave principal", "codigo_comuna", "outputs/resumen_homologacion.md; src/comunas.py"],
        ["Naturaleza analítica", "Comparativa y descriptiva, no causal", "README.md; outputs/analisis_exploratorio.md"],
        ["Temporalidad", "Pobreza 2022; población, áreas verdes e IPP 2024", "data/raw/metadata_fuentes.csv; outputs/resumen_dataset_final.md"],
        ["Integración", "Merges left con validación one_to_one sobre codigo_comuna", "outputs/log_integracion.md; src/integrate.py"],
        ["Tratamiento de faltantes", "Sin imputación; métricas derivadas quedan NA solo si la división es inválida", "outputs/resumen_dataset_final.md; src/integrate.py"],
        ["Producto final", "CSV final, SQLite y outputs analíticos reproducibles", "README.md; outputs/reporte_carga_sqlite.md"],
    ]
    write_text(
        TABLAS_DIR / "tabla_decisiones_metodologicas.tex",
        latex_table(
            caption="Decisiones metodológicas observadas en el repositorio.",
            label="tab:decisiones_metodologicas",
            colspec="|p{3.0cm}|p{5.6cm}|p{5.0cm}|",
            headers=["Dimensión", "Decisión observada", "Evidencia principal"],
            rows=tabla_decisiones_rows,
        ),
    )

    tabla_perfilado_rows = []
    for _, row in perfilado_resumen.iterrows():
        tabla_perfilado_rows.append(
            [
                row["source_id"],
                row["nombre_fuente"],
                row["filas"],
                row["columnas"],
                row["duplicados_fila"],
                row["filas_totalmente_nulas"],
                f"{row['formato']} / {row['parser']}",
            ]
        )
    write_text(
        TABLAS_DIR / "tabla_perfilado_resumen.tex",
        latex_table(
            caption="Perfilado resumido de las cuatro fuentes según el workbook de Fase 2.",
            label="tab:perfilado_resumen",
            colspec="|c|p{3.3cm}|r|r|r|r|p{4.0cm}|",
            headers=["ID", "Fuente", "Filas", "Cols.", "Dup.", "Filas nulas", "Formato y parser"],
            rows=tabla_perfilado_rows,
        ),
    )

    conflicto_rows = []
    conflict_data = {
        "A": ("52", "32", "20", "6", "Valores especiales No Aplica y No Recepcionado; encabezado extendido."),
        "B": ("52", "32", "20", "6", "Encabezado extendido y diferencias ortográficas en nombres."),
        "C": ("345", "32", "313", "32", "Seis filas de nota o blanco; pobreza reportada como proporción 0-1."),
        "D": ("347", "32", "315", "32", "Fila País y dos filas no comunales; columnas extra de sexo."),
    }
    fuentes_nombre = metadata.set_index("id_fuente")["nombre_fuente"].to_dict()
    for source_id, (validos, dentro, fuera, difs, nota) in conflict_data.items():
        conflicto_rows.append([source_id, fuentes_nombre[source_id], validos, dentro, fuera, difs, nota])
    write_text(
        TABLAS_DIR / "tabla_conflictos_integracion.tex",
        latex_table(
            caption="Conflictos de integración identificados durante el perfilado y la homologación.",
            label="tab:conflictos_integracion",
            colspec="|c|p{3.3cm}|r|r|r|r|p{4.2cm}|",
            headers=["ID", "Fuente", "Códigos válidos", "En universo", "Fuera de alcance", "Dif. nombre", "Observación"],
            rows=conflicto_rows,
        ),
    )

    homologacion_ejemplos = homologacion[
        homologacion["tipo_diferencia"] == "coincidencia_por_normalizacion"
    ].copy()
    homologacion_ejemplos = homologacion_ejemplos[
        homologacion_ejemplos["fuente"].isin(["A", "B", "C", "D"])
    ].head(8)
    homologacion_rows = []
    for _, row in homologacion_ejemplos.iterrows():
        homologacion_rows.append(
            [
                row["fuente"],
                row["codigo_comuna"],
                row["nombre_comuna_base"],
                row["nombre_fuente"],
                row["tipo_diferencia"].replace("_", " "),
            ]
        )
    write_text(
        TABLAS_DIR / "tabla_homologacion_ejemplos.tex",
        latex_table(
            caption="Ejemplos reales de homologación resuelta por normalización automática.",
            label="tab:homologacion_ejemplos",
            colspec="|c|c|p{3.0cm}|p{3.0cm}|p{4.5cm}|",
            headers=["Fuente", "Código", "Nombre base", "Nombre observado", "Resolución"],
            rows=homologacion_rows,
        ),
    )

    modelo_rows = [
        [
            "dim_comuna",
            "Dimensión de comunas del universo final.",
            "codigo_comuna",
            len(sqlite_schema["dim_comuna"]),
            sqlite_counts["dim_comuna"],
            "Conserva nombre, provincia, región y fuente_referencia.",
        ],
        [
            "fact_desigualdad_comunal",
            "Tabla de hechos con variables finales y métricas derivadas.",
            "codigo_comuna",
            len(sqlite_schema["fact_desigualdad_comunal"]),
            sqlite_counts["fact_desigualdad_comunal"],
            "No replica nombre_comuna; se relaciona con dim_comuna.",
        ],
        [
            "metadata_fuentes",
            "Contrato operativo y trazabilidad de lectura de fuentes.",
            "id_fuente",
            len(sqlite_schema["metadata_fuentes"]),
            sqlite_counts["metadata_fuentes"],
            "Documenta institución, URL, hoja, skiprows y archivo lógico.",
        ],
    ]
    write_text(
        TABLAS_DIR / "tabla_modelo_datos.tex",
        latex_table(
            caption="Resumen del modelo físico observado en SQLite.",
            label="tab:modelo_datos",
            colspec="|p{3.5cm}|p{4.2cm}|p{2.2cm}|r|r|p{3.2cm}|",
            headers=["Tabla", "Rol", "Llave primaria", "Cols.", "Filas", "Observación"],
            rows=modelo_rows,
        ),
    )

    mapa_logico_rows = [
        ["Todas", "codigo_comuna / Código / Código comuna", "Parseo numérico y formateo string de 5 dígitos", "codigo_comuna"],
        ["A", "mmpqc_2024 + mmpzc_2024", "No Aplica -> 0; No Recepcionado -> NA; suma con min_count=2", "areas_verdes_m2"],
        ["B", "iadm41_2024", "Renombre y conservación en miles de pesos nominales 2024", "ipp_miles_pesos"],
        ["C", "Porcentaje de personas en situación de pobreza por ingresos 2022", "Conversión de proporción 0-1 a porcentaje 0-100 y redondeo", "pobreza_ingresos_pct"],
        ["D", "Población censada", "Selección, tipificación Int64 y filtrado por universo", "poblacion"],
        ["Fase 6", "Constantes de referencia", "Asignación explícita de años de referencia por variable", "anio_poblacion / anio_pobreza / anio_areas_verdes / anio_ingresos"],
        ["Fase 6", "areas_verdes_m2 + poblacion", "División controlada con población > 0", "areas_verdes_m2_hab"],
        ["Fase 6", "ipp_miles_pesos + poblacion", "Conversión a pesos por habitante y control de infinitos", "ipp_pesos_hab"],
    ]
    write_text(
        TABLAS_DIR / "tabla_mapa_logico_resumido.tex",
        latex_table(
            caption="Mapa lógico resumido desde origen hasta variable final.",
            label="tab:mapa_logico_resumido",
            colspec="|p{1.2cm}|p{4.0cm}|p{5.5cm}|p{3.4cm}|",
            headers=["Fase/fuente", "Origen", "Transformación", "Destino final"],
            rows=mapa_logico_rows,
        ),
    )

    tabla_transformaciones_rows = [
        ["Selección de columnas", "A-D", "Solo se conservan campos comunales y variables de interés.", "outputs/resumen_transformaciones.md"],
        ["Normalización comunal", "A-D", "Estandarización de nombre_comuna contra dim_comuna_base.csv.", "outputs/resumen_transformaciones.md; outputs/homologacion_comunas.csv"],
        ["Formateo de llave", "A-D", "codigo_comuna se tipifica y luego se fija como string de 5 dígitos.", "src/transform.py; src/integrate.py"],
        ["Tratamiento de valores especiales", "A", "No Aplica -> 0 y No Recepcionado -> NA en componentes de áreas verdes.", "outputs/conflictos_fuentes.md; src/transform.py"],
        ["Conversión de escala", "C", "La pobreza se transforma desde proporción 0-1 a porcentaje 0-100.", "data/raw/metadata_fuentes.csv; src/transform.py"],
        ["Filtrado territorial", "A-D", "Se excluyen comunas fuera de la Provincia de Santiago y filas sin código válido.", "outputs/resumen_transformaciones.md"],
        ["Renombre semántico", "B-D", "iadm41_2024 -> ipp_miles_pesos; Población censada -> poblacion.", "src/transform.py"],
        ["Métricas derivadas", "Fase 6", "Se calculan areas_verdes_m2_hab e ipp_pesos_hab con control de población > 0.", "outputs/resumen_dataset_final.md; src/integrate.py"],
        ["Validaciones de rango", "A-D", "Población > 0; pobreza 0-100; áreas verdes e IPP no negativos.", "outputs/validacion_staging.csv; outputs/reporte_validacion_final.csv"],
        ["Control de cardinalidad", "Fase 6", "Todos los merges se ejecutan como left con validación one_to_one.", "outputs/log_integracion.md; src/integrate.py"],
    ]
    write_text(
        TABLAS_DIR / "tabla_transformaciones.tex",
        latex_table(
            caption="Transformaciones y controles relevantes observados en el ETL.",
            label="tab:transformaciones",
            colspec="|p{2.7cm}|p{1.2cm}|p{7.0cm}|p{3.5cm}|",
            headers=["Transformación", "Fuente", "Regla aplicada", "Evidencia"],
            rows=tabla_transformaciones_rows,
        ),
    )

    validation_checks = validacion_final[validacion_final["categoria"] == "check"].copy()
    selected_check_ids = [
        "fila_por_comuna",
        "codigo_comuna_unico",
        "cantidad_comunas",
        "cobertura_dim_base",
        "convertibilidad_numerica",
        "poblacion_positiva",
        "pobreza_rango",
        "areas_verdes_no_negativas",
        "ipp_no_negativo",
        "areas_verdes_m2_hab_sin_inf",
        "ipp_pesos_hab_sin_inf",
        "apto_para_sqlite",
    ]
    validation_checks = validation_checks[validation_checks["check_id"].isin(selected_check_ids)]
    tabla_validacion_rows = []
    for _, row in validation_checks.iterrows():
        tabla_validacion_rows.append(
            [row["check_id"], row["descripcion"], row["resultado"], row["valor_observado"], row["detalle"]]
        )
    write_text(
        TABLAS_DIR / "tabla_validacion_resumen.tex",
        latex_table(
            caption="Resumen de validaciones estructurales y de rango del dataset final.",
            label="tab:validacion_resumen",
            colspec="|p{2.4cm}|p{5.0cm}|c|p{3.2cm}|p{3.4cm}|",
            headers=["Check", "Descripción", "Resultado", "Valor observado", "Detalle"],
            rows=tabla_validacion_rows,
            size=r"\scriptsize",
        ),
    )

    sqlite_count_rows = [
        ["dim_comuna", sqlite_counts["dim_comuna"], "Dimensión comunal"],
        ["fact_desigualdad_comunal", sqlite_counts["fact_desigualdad_comunal"], "Tabla de hechos"],
        ["metadata_fuentes", sqlite_counts["metadata_fuentes"], "Contrato operativo de fuentes"],
    ]
    write_text(
        TABLAS_DIR / "tabla_sqlite_conteos.tex",
        latex_table(
            caption="Conteo de filas por tabla en la base SQLite final.",
            label="tab:sqlite_conteos",
            colspec="|p{4.2cm}|r|p{6.0cm}|",
            headers=["Tabla", "Filas", "Rol"],
            rows=sqlite_count_rows,
        ),
    )

    consulta_rows = []
    subset = consultas_sqlite[
        consultas_sqlite["consulta"].isin(
            [
                "conteo_filas_por_tabla",
                "top_5_menor_areas_verdes_m2_hab",
                "top_5_mayor_pobreza_ingresos_pct",
                "top_5_menor_ipp_pesos_hab",
            ]
        )
    ].copy()
    for _, row in subset.iterrows():
        consulta_rows.append(
            [
                row["consulta"],
                row["orden"] or "-",
                row["tabla"],
                row["codigo_comuna"] or "-",
                row["nombre_comuna"] or "-",
                row["valor"],
                row["detalle"],
            ]
        )
    write_text(
        TABLAS_DIR / "tabla_sqlite_consultas_prueba.tex",
        latex_table(
            caption="Consultas de prueba documentadas tras la carga en SQLite.",
            label="tab:sqlite_consultas",
            colspec="|p{3.2cm}|p{0.9cm}|p{3.0cm}|p{1.2cm}|p{2.8cm}|p{2.3cm}|p{1.8cm}|",
            headers=["Consulta", "Ord.", "Tabla", "Código", "Comuna", "Valor", "Detalle"],
            rows=consulta_rows,
            size=r"\scriptsize",
        ),
    )

    hallazgos_rows = [
        [
            "Menor áreas verdes por habitante",
            ", ".join(ctx["top_bottom_areas"]["nombre_comuna"].astype(str).tolist()),  # type: ignore[index]
            "outputs/ranking_areas_verdes.csv",
        ],
        [
            "Mayor pobreza por ingresos",
            ", ".join(ctx["top_pobreza"]["nombre_comuna"].astype(str).tolist()),  # type: ignore[index]
            "outputs/ranking_pobreza.csv",
        ],
        [
            "Menor IPP por habitante",
            ", ".join(ctx["top_ipp"]["nombre_comuna"].astype(str).tolist()),  # type: ignore[index]
            "outputs/ranking_ipp.csv",
        ],
        [
            "Peor quintil simultáneo de pobreza y áreas verdes",
            ", ".join(ctx["peor_pobreza_areas"]["nombre_comuna"].astype(str).tolist()),  # type: ignore[index]
            "outputs/tablas_hallazgos_fase9.csv",
        ],
        [
            "Peor quintil simultáneo de pobreza e IPP",
            ", ".join(ctx["peor_pobreza_ipp"]["nombre_comuna"].astype(str).tolist()),  # type: ignore[index]
            "outputs/tablas_hallazgos_fase9.csv",
        ],
        [
            "Rezago crítico en al menos dos dimensiones",
            ", ".join(ctx["rezagadas_multidim"]["nombre_comuna"].astype(str).tolist()),  # type: ignore[index]
            "outputs/indice_rezago_territorial.csv",
        ],
    ]
    write_text(
        TABLAS_DIR / "tabla_hallazgos_resumen.tex",
        latex_table(
            caption="Resumen de hallazgos descriptivos reutilizables desde los outputs de Fase 9.",
            label="tab:hallazgos_resumen",
            colspec="|p{4.3cm}|p{7.0cm}|p{3.0cm}|",
            headers=["Hallazgo", "Comunas observadas", "Output fuente"],
            rows=hallazgos_rows,
        ),
    )

    diccionario_rows = [
        ["codigo_comuna", "string(5)", "Llave maestra comunal.", "dim_comuna_base / todas las fuentes"],
        ["nombre_comuna", "string", "Nombre oficial de la base maestra.", "dim_comuna_base"],
        ["poblacion", "int", "Población censada comunal.", "Fuente D / Censo 2024"],
        ["anio_poblacion", "int", "Año de referencia de población.", "Constante Fase 6"],
        ["pobreza_ingresos_pct", "float", "Porcentaje de pobreza por ingresos.", "Fuente C / Observatorio Social"],
        ["anio_pobreza", "int", "Año de referencia de pobreza.", "Constante Fase 6"],
        ["areas_verdes_m2", "int", "Superficie total de áreas verdes comunales.", "Fuente A / SINIM"],
        ["anio_areas_verdes", "int", "Año de referencia de áreas verdes.", "Constante Fase 6"],
        ["ipp_miles_pesos", "int", "Ingresos propios permanentes en miles de pesos.", "Fuente B / SINIM"],
        ["anio_ingresos", "int", "Año de referencia del IPP.", "Constante Fase 6"],
        ["areas_verdes_m2_hab", "float", "Áreas verdes por habitante.", "Derivada Fase 6"],
        ["ipp_pesos_hab", "float", "IPP en pesos por habitante.", "Derivada Fase 6"],
    ]
    write_text(
        TABLAS_DIR / "tabla_diccionario_datos_final.tex",
        latex_table(
            caption="Diccionario resumido del dataset final integrado.",
            label="tab:diccionario_datos_final",
            colspec="|p{3.2cm}|p{1.8cm}|p{5.5cm}|p{3.5cm}|",
            headers=["Variable", "Tipo", "Descripción", "Origen"],
            rows=diccionario_rows,
        ),
    )

    mapa_extendido_rows = [
        ["data/raw/metadata_fuentes.csv", "Contrato operativo de lectura", "Define archivo, hoja, skiprows y observaciones por fuente", "Fases 2 y 4"],
        ["data/raw/dim_comuna_base.csv", "Universo maestro", "Restringe cobertura a 32 comunas y aporta nombre oficial", "Fases 3, 5 y 6"],
        ["data/staging/poblacion_staging.csv", "Staging D", "codigo_comuna, nombre_comuna, poblacion", "Fase 6 / merge 1"],
        ["data/staging/pobreza_staging.csv", "Staging C", "codigo_comuna, nombre_comuna, pobreza_ingresos_pct", "Fase 6 / merge 2"],
        ["data/staging/areas_verdes_staging.csv", "Staging A", "codigo_comuna, nombre_comuna, mmpqc_2024, mmpzc_2024, areas_verdes_m2", "Fase 6 / merge 3"],
        ["data/staging/ingresos_staging.csv", "Staging B", "codigo_comuna, nombre_comuna, ipp_miles_pesos", "Fase 6 / merge 4"],
        ["data/processed/desigualdad_comunal_final.csv", "Dataset final", "12 columnas finales y una fila por comuna", "Fases 7, 8 y 9"],
        ["db/lab1_desigualdad.sqlite", "Persistencia final", "dim_comuna, fact_desigualdad_comunal, metadata_fuentes", "Fase 8"],
    ]
    write_text(
        TABLAS_DIR / "tabla_mapa_logico_extendido.tex",
        latex_table(
            caption="Mapa lógico extendido de artefactos y destinos del ETL.",
            label="tab:mapa_logico_extendido",
            colspec="|p{4.3cm}|p{2.5cm}|p{5.2cm}|p{2.4cm}|",
            headers=["Artefacto", "Tipo", "Contenido relevante", "Fase de uso"],
            rows=mapa_extendido_rows,
        ),
    )

    homologacion_resumen_rows = []
    for _, row in homologacion_summary.sort_values("fuente").iterrows():
        homologacion_resumen_rows.append(
            [
                row["fuente"],
                int(row["coincidencia_exacta"]),
                int(row["coincidencia_por_normalizacion"]),
                int(row["coincidencia_por_homologacion_manual"]),
                int(row["requiere_homologacion_manual"]),
            ]
        )
    write_text(
        TABLAS_DIR / "tabla_homologacion_resumen_fuente.tex",
        latex_table(
            caption="Resumen por fuente de la homologación dentro del universo final.",
            label="tab:homologacion_resumen_fuente",
            colspec="|c|r|r|r|r|",
            headers=["Fuente", "Exactas", "Por normalización", "Manual", "Pendientes"],
            rows=homologacion_resumen_rows,
        ),
    )

    rezago_rows = []
    rezago_df: pd.DataFrame = ctx["rezagadas_multidim"]  # type: ignore[assignment]
    for _, row in rezago_df.iterrows():
        rezago_rows.append(
            [
                row["codigo_comuna"],
                row["nombre_comuna"],
                format_decimal(row["pobreza_ingresos_pct"], 4),
                format_decimal(row["areas_verdes_m2_hab"], 6),
                format_decimal(row["ipp_pesos_hab"], 6),
                int(row["dimensiones_rezago_critico"]),
                int(row["indice_rezago_territorial"]),
            ]
        )
    write_text(
        TABLAS_DIR / "tabla_rezagadas_multidimensionales.tex",
        latex_table(
            caption="Comunas con rezago crítico en al menos dos dimensiones del análisis auxiliar.",
            label="tab:rezagadas_multidimensionales",
            colspec="|c|p{3.0cm}|p{1.6cm}|p{2.0cm}|p{2.2cm}|c|c|",
            headers=["Código", "Comuna", "Pobreza", "Áreas/hab", "IPP/hab", "Dim.", "Índice"],
            rows=rezago_rows,
            size=r"\scriptsize",
        ),
    )


def copy_figures() -> None:
    for filename in FIGURE_FILES:
        shutil.copy2(OUTPUTS_FIGURES_DIR / filename, FIGURAS_DIR / filename)


def create_manifest_figuras(ctx: dict[str, object]) -> None:
    quilicura_value = format_decimal(ctx["quilicura_row"]["areas_verdes_m2_hab"], 6)  # type: ignore[index]
    la_reina_value = format_decimal(ctx["la_reina_row"]["areas_verdes_m2_hab"], 6)  # type: ignore[index]
    providencia_value = format_decimal(ctx["providencia_row"]["areas_verdes_m2_hab"], 6)  # type: ignore[index]
    content = textwrap.dedent(
        f"""
        # Manifiesto de figuras

        | Figura | Archivo origen | Sección sugerida | Caption sugerido | Nota metodológica |
        | --- | --- | --- | --- | --- |
        | Figura 1 | `outputs/figures/areas_verdes_m2_hab_bottom10.png` | Sección 12 | Diez comunas con menor disponibilidad de áreas verdes por habitante en el dataset final. | Orden ascendente por `areas_verdes_m2_hab`. |
        | Figura 2 | `outputs/figures/pobreza_ingresos_top10.png` | Sección 12 | Diez comunas con mayor pobreza por ingresos en el dataset final. | Orden descendente por `pobreza_ingresos_pct`. |
        | Figura 3 | `outputs/figures/ipp_pesos_hab_bottom10.png` | Sección 12 | Diez comunas con menor IPP por habitante en el dataset final. | Orden ascendente por `ipp_pesos_hab`. |
        | Figura 4 | `outputs/figures/pobreza_vs_areas_verdes_scatter.png` | Sección 12 | Relación descriptiva entre pobreza por ingresos y áreas verdes por habitante. | El eje X se dejó en escala logarítmica por el caso de Quilicura (`{quilicura_value}`), muy por encima de La Reina (`{la_reina_value}`) y Providencia (`{providencia_value}`). |
        | Figura 5 | `outputs/figures/indice_rezago_territorial_top10.png` | Sección 12 | Diez comunas con mayor índice auxiliar de rezago territorial. | El índice es un apoyo analítico construido en Fase 9 y no una variable oficial de fuente. |
        """
    ).strip()
    write_text(FIGURAS_DIR / "manifest_figuras.md", content)


def create_metadatos() -> None:
    content = textwrap.dedent(
        """
        # Metadatos sugeridos para `datos.tex`

        ## Propuesta de carga

        - Título del informe: `Desigualdad territorial en Santiago: áreas verdes, pobreza por ingresos y capacidad municipal por comuna`
        - Subtítulo opcional: `Lab 1 - Proceso ETL`
        - Tipo de informe: `Informe técnico-metodológico`
        - Curso: `Inteligencia de Negocios`
        - Laboratorio: `Lab 1 - Proceso ETL`
        - Carrera: `TODO: insumo no encontrado en el repo`
        - Docente: `TODO: insumo no encontrado en el repo`
        - Autores: `TODO: completar nombres y apellidos`
        - Fecha: `TODO: completar fecha de entrega`

        ## Observaciones de montaje

        - Mantener la estructura relativa `Secciones/`, `Tablas/`, `Figuras/` y `Anexos/` al mover estos materiales al template.
        - `Resumen.tex` ya incluye `\\chapter*{Resumen Ejecutivo}` y `\\addcontentsline`.
        - Las tablas `.tex` están preparadas para ser llamadas con `\\input{Tablas/...}`.
        - Las figuras fueron copiadas a `Figuras/` con los mismos nombres de `outputs/figures/`.
        - `referencias_lab1.bib` se construyó solo con datos realmente presentes en `data/raw/metadata_fuentes.csv`.
        - Si el template usa otro archivo de metadatos, traspasar estos campos sin reinterpretar años, coberturas ni nombres de variables.
        """
    ).strip()
    write_text(DOCS_DIR / "00_metadatos_sugeridos.md", content)


def create_readme_handoff() -> None:
    content = textwrap.dedent(
        """
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

        - Las secciones llaman tablas con `\\input{Tablas/...}`.
        - Las secciones llaman figuras con `\\includegraphics{Figuras/...}`.
        - Si se preserva esta estructura al copiar, no deberían requerirse cambios de rutas.

        ## Alcance del paquete

        - No modifica el template externo.
        - No reescribe Fases 1 a 9.
        - No altera `data/raw/`, el pipeline ETL ni la llave `codigo_comuna`.
        - No agrega resultados no respaldados por evidencia del repositorio.
        """
    ).strip()
    write_text(DOCS_DIR / "README_handoff_template.md", content)


def create_referencias(ctx: dict[str, object]) -> None:
    metadata: pd.DataFrame = ctx["metadata"]  # type: ignore[assignment]
    entries = []
    keys = {
        "A": "sinimAreasVerdes2024",
        "B": "sinimCapacidadMunicipal2024",
        "C": "observatorioPobreza2022",
        "D": "censoPoblacion2024",
    }
    for _, row in metadata.iterrows():
        bibkey = keys[row["id_fuente"]]
        note = (
            f"Archivo versionado: {row['archivo_origen']}. "
            f"Archivo lógico: {row['archivo_logico']}. "
            f"Hoja: {row['hoja']}. "
            f"skiprows: {row['skiprows']}. "
            f"Fecha de descarga registrada: {row['fecha_descarga']}."
        )
        entry = (
            "@misc{"
            + bibkey
            + ",\n"
            + f"  title = {{{row['nombre_fuente']}}},\n"
            + f"  author = {{{row['institucion']}}},\n"
            + f"  year = {{{row['anio_referencia']}}},\n"
            + f"  url = {{{row['url']}}},\n"
            + f"  note = {{{note}}}\n"
            + "}"
        )
        entries.append(entry)
    write_text(DOCS_DIR / "referencias_lab1.bib", "\n\n".join(entries))


def create_traceability() -> None:
    rows = [
        {
            "seccion": "Resumen Ejecutivo",
            "archivo_salida": "Resumen.tex",
            "afirmacion_o_bloque": "Síntesis de problema, fuentes, ETL, dataset final, SQLite y hallazgos descriptivos.",
            "archivo_fuente_principal": "outputs/analisis_exploratorio.md",
            "archivo_fuente_secundario": "outputs/reporte_carga_sqlite.md",
            "tipo_evidencia": "reportes markdown + CSV final",
            "observaciones": "Cruza dataset, carga y outputs de Fase 9.",
        },
        {
            "seccion": "Introducción",
            "archivo_salida": "Secciones/01_introduccion.tex",
            "afirmacion_o_bloque": "Contexto del problema, dimensiones del proyecto y necesidad de integración.",
            "archivo_fuente_principal": "README.md",
            "archivo_fuente_secundario": "data/raw/metadata_fuentes.csv",
            "tipo_evidencia": "documentación del repo + metadata",
            "observaciones": "No agrega resultados analíticos.",
        },
        {
            "seccion": "Objetivos",
            "archivo_salida": "Secciones/02_objetivos.tex",
            "afirmacion_o_bloque": "Objetivos coherentes con lo ejecutado en Fases 1 a 9.",
            "archivo_fuente_principal": "README.md",
            "archivo_fuente_secundario": "src/main.py",
            "tipo_evidencia": "documentación y orquestación del pipeline",
            "observaciones": "Refleja etapas realmente implementadas.",
        },
        {
            "seccion": "Alcance y decisiones metodológicas",
            "archivo_salida": "Secciones/03_alcance_decisiones_metodologicas.tex",
            "afirmacion_o_bloque": "Cobertura, unidad de análisis, llave principal, temporalidad y naturaleza descriptiva.",
            "archivo_fuente_principal": "outputs/resumen_dataset_final.md",
            "archivo_fuente_secundario": "outputs/resumen_homologacion.md",
            "tipo_evidencia": "reportes markdown",
            "observaciones": "Incluye años de referencia observados.",
        },
        {
            "seccion": "Fuentes",
            "archivo_salida": "Secciones/04_fuentes.tex",
            "afirmacion_o_bloque": "Descripción por fuente, formato, hoja, variable y aporte.",
            "archivo_fuente_principal": "data/raw/metadata_fuentes.csv",
            "archivo_fuente_secundario": "outputs/perfilado_fuentes.xlsx",
            "tipo_evidencia": "metadata + workbook de perfilado",
            "observaciones": "No inventa fichas bibliográficas externas.",
        },
        {
            "seccion": "Perfilado y diagnóstico",
            "archivo_salida": "Secciones/05_perfilado_diagnostico.tex",
            "afirmacion_o_bloque": "Filas, columnas, conflictos y problemas de calidad por fuente.",
            "archivo_fuente_principal": "outputs/perfilado_fuentes.xlsx",
            "archivo_fuente_secundario": "outputs/conflictos_fuentes.md",
            "tipo_evidencia": "workbook + reporte markdown",
            "observaciones": "Resume sin volcar el Excel completo.",
        },
        {
            "seccion": "Llave maestra",
            "archivo_salida": "Secciones/06_llave_maestra.tex",
            "afirmacion_o_bloque": "Justificación de codigo_comuna, universo final y ejemplos de homologación.",
            "archivo_fuente_principal": "outputs/homologacion_comunas.csv",
            "archivo_fuente_secundario": "outputs/resumen_homologacion.md",
            "tipo_evidencia": "CSV de homologación + resumen",
            "observaciones": "No reporta homologaciones manuales inexistentes.",
        },
        {
            "seccion": "Modelo de datos",
            "archivo_salida": "Secciones/07_modelo_datos.tex",
            "afirmacion_o_bloque": "Descripción real de dim_comuna, fact_desigualdad_comunal y metadata_fuentes.",
            "archivo_fuente_principal": "db/lab1_desigualdad.sqlite",
            "archivo_fuente_secundario": "outputs/reporte_carga_sqlite.md",
            "tipo_evidencia": "SQLite + reporte markdown",
            "observaciones": "Respeta que nombre_comuna vive en la dimensión.",
        },
        {
            "seccion": "Mapa lógico",
            "archivo_salida": "Secciones/08_mapa_logico.tex",
            "afirmacion_o_bloque": "Origen, transformación y destino de las variables finales.",
            "archivo_fuente_principal": "src/transform.py",
            "archivo_fuente_secundario": "src/integrate.py",
            "tipo_evidencia": "código fuente",
            "observaciones": "Se contrasta con staging y dataset final.",
        },
        {
            "seccion": "Desarrollo ETL",
            "archivo_salida": "Secciones/09_desarrollo_etl.tex",
            "afirmacion_o_bloque": "Extracción, transformación, integración y reproducibilidad.",
            "archivo_fuente_principal": "src/main.py",
            "archivo_fuente_secundario": "outputs/resumen_transformaciones.md",
            "tipo_evidencia": "código fuente + reportes",
            "observaciones": "Incluye soporte a python src/main.py y python -m src.main.",
        },
        {
            "seccion": "Validación del dataset final",
            "archivo_salida": "Secciones/10_validacion_dataset.tex",
            "afirmacion_o_bloque": "Unicidad, cobertura, convertibilidad, rangos y ausencia de infinitos.",
            "archivo_fuente_principal": "outputs/reporte_validacion_final.csv",
            "archivo_fuente_secundario": "outputs/reporte_validacion_final.md",
            "tipo_evidencia": "CSV y markdown de validación",
            "observaciones": "Se apoya en el CSV final real.",
        },
        {
            "seccion": "Carga SQLite",
            "archivo_salida": "Secciones/11_carga_sqlite.tex",
            "afirmacion_o_bloque": "Conteos por tabla, quick_check y consultas de prueba.",
            "archivo_fuente_principal": "outputs/reporte_carga_sqlite.md",
            "archivo_fuente_secundario": "outputs/reporte_consultas_sqlite.csv",
            "tipo_evidencia": "markdown + CSV de consultas",
            "observaciones": "Describe la base tal como existe.",
        },
        {
            "seccion": "Resultados y análisis",
            "archivo_salida": "Secciones/12_resultados_analisis.tex",
            "afirmacion_o_bloque": "Rankings, cruces descriptivos, índice auxiliar y outlier de Quilicura.",
            "archivo_fuente_principal": "outputs/tablas_hallazgos_fase9.csv",
            "archivo_fuente_secundario": "outputs/analisis_exploratorio.md",
            "tipo_evidencia": "CSV de hallazgos + reporte analítico + figuras",
            "observaciones": "Sin inferencia causal.",
        },
        {
            "seccion": "Limitaciones",
            "archivo_salida": "Secciones/13_limitaciones.tex",
            "afirmacion_o_bloque": "Años heterogéneos, índice auxiliar, dependencia de definiciones y outliers.",
            "archivo_fuente_principal": "outputs/analisis_exploratorio.md",
            "archivo_fuente_secundario": "outputs/evaluacion_corta_fase9.md",
            "tipo_evidencia": "reportes markdown",
            "observaciones": "Limita interpretación del scatter.",
        },
        {
            "seccion": "Conclusiones",
            "archivo_salida": "Secciones/14_conclusiones.tex",
            "afirmacion_o_bloque": "Cierre técnico del ETL y valor del dataset/SQLite como productos reutilizables.",
            "archivo_fuente_principal": "README.md",
            "archivo_fuente_secundario": "outputs/reporte_carga_sqlite.md",
            "tipo_evidencia": "documentación + reportes",
            "observaciones": "Conclusión descriptiva y técnica.",
        },
        {
            "seccion": "Anexos",
            "archivo_salida": "Anexos/anexos.tex",
            "afirmacion_o_bloque": "Diccionario de datos, perfilado, homologación, validación, SQLite y revisión de Fase 9.",
            "archivo_fuente_principal": "outputs/perfilado_fuentes.xlsx",
            "archivo_fuente_secundario": "outputs/evaluacion_corta_fase9.md",
            "tipo_evidencia": "outputs y tablas auxiliares",
            "observaciones": "Reúne evidencias extendidas del informe.",
        },
    ]
    with (DOCS_DIR / "trazabilidad_informe.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "seccion",
                "archivo_salida",
                "afirmacion_o_bloque",
                "archivo_fuente_principal",
                "archivo_fuente_secundario",
                "tipo_evidencia",
                "observaciones",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def build_resumen(ctx: dict[str, object]) -> str:
    dataset_rows = ctx["dataset_rows"]
    dataset_cols = ctx["dataset_cols"]
    sqlite_counts: dict[str, int] = ctx["sqlite_counts"]  # type: ignore[assignment]
    top_areas = ", ".join(ctx["top_bottom_areas"]["nombre_comuna"].astype(str).tolist())  # type: ignore[index]
    top_pobreza = ", ".join(ctx["top_pobreza"]["nombre_comuna"].astype(str).tolist())  # type: ignore[index]
    top_ipp = ", ".join(ctx["top_ipp"]["nombre_comuna"].astype(str).tolist())  # type: ignore[index]
    rezagadas = ", ".join(ctx["rezagadas_multidim"]["nombre_comuna"].astype(str).tolist())  # type: ignore[index]
    quilicura_value = format_decimal(ctx["quilicura_row"]["areas_verdes_m2_hab"], 6)  # type: ignore[index]
    la_reina_value = format_decimal(ctx["la_reina_row"]["areas_verdes_m2_hab"], 6)  # type: ignore[index]

    return textwrap.dedent(
        f"""
        \\chapter*{{Resumen Ejecutivo}}
        \\addcontentsline{{toc}}{{chapter}}{{Resumen Ejecutivo}}

        Este informe documenta el proceso ETL aplicado al estudio descriptivo de desigualdad territorial en la Provincia de Santiago, integrando cuatro fuentes públicas sobre áreas verdes comunales, pobreza por ingresos, capacidad municipal e información poblacional. La integración se resolvió sobre la llave \\texttt{{codigo\\_comuna}}, debido a que los nombres de comuna difieren entre fuentes en mayúsculas, tildes y estilo de escritura. El repositorio evidencia un flujo reproducible desde perfilado y homologación hasta transformación, integración, validación final, carga a SQLite y análisis exploratorio.

        El producto integrado observado en el repositorio corresponde a \\texttt{{data/processed/desigualdad\\_comunal\\_final.csv}}, con {dataset_rows} filas y {dataset_cols} columnas, una fila por comuna y cobertura completa de las 32 comunas del universo definido. La validación formal reporta ausencia de duplicados por \\texttt{{codigo\\_comuna}}, ausencia de nulos en las columnas finales, convertibilidad numérica sin errores, rangos consistentes para pobreza, áreas verdes e IPP, y ausencia de infinitos en las métricas derivadas por habitante. La carga final en \\texttt{{db/lab1\\_desigualdad.sqlite}} materializa tres tablas: \\texttt{{dim\\_comuna}} ({sqlite_counts["dim_comuna"]} filas), \\texttt{{fact\\_desigualdad\\_comunal}} ({sqlite_counts["fact_desigualdad_comunal"]} filas) y \\texttt{{metadata\\_fuentes}} ({sqlite_counts["metadata_fuentes"]} filas), con \\texttt{{PRAGMA quick\\_check = ok}}.

        En los outputs de Fase 9 se observan, entre otros resultados descriptivos, menores disponibilidades relativas de áreas verdes en {top_areas}; mayores niveles observados de pobreza por ingresos en {top_pobreza}; y menores niveles de IPP por habitante en {top_ipp}. El cruce por quintiles identifica rezago crítico en al menos dos dimensiones para {rezagadas}. Además, Quilicura aparece como outlier plausible en \\texttt{{areas\\_verdes\\_m2\\_hab}} con {quilicura_value}, muy por encima del siguiente valor observado en La Reina ({la_reina_value}), razón por la cual el scatter de pobreza y áreas verdes se documenta con escala logarítmica en el eje X. En conjunto, el dataset final y la base SQLite quedan listos como productos reutilizables para consulta, auditoría metodológica y montaje posterior del informe en el template externo.
        """
    ).strip()


def build_section_01() -> str:
    return textwrap.dedent(
        """
        \\chapter{Introducción}

        El problema abordado en este laboratorio corresponde a la descripción comparativa de desigualdad territorial entre comunas de la Provincia de Santiago, usando tres dimensiones sustantivas: disponibilidad de áreas verdes, pobreza por ingresos y capacidad municipal. La unidad de análisis observada en el proyecto es comunal, por lo que cada registro final representa una comuna y resume variables provenientes de distintas instituciones públicas.

        La construcción de un proceso ETL resulta necesaria porque las fuentes disponibles no llegan en un formato analítico homogéneo. En el repositorio se observan diferencias de formato de archivo, estructuras de encabezado, escalas de medición y variantes ortográficas en \\texttt{nombre\\_comuna}. En particular, dos fuentes SINIM fueron publicadas como archivos con extensión \\texttt{.xls} pero estructura SpreadsheetML/XML 2003, mientras que las otras dos corresponden a libros \\texttt{.xlsx}. Adicionalmente, los nombres comunales cambian entre mayúsculas, tildes y escritura capitalizada, lo que vuelve insuficiente cualquier integración basada en nombre crudo.

        El enfoque ETL implementado en el proyecto separa explícitamente las etapas de perfilado, homologación, extracción a staging, transformación por fuente, integración final, validación estructural, carga a SQLite y análisis exploratorio. Esta secuencia permite preservar trazabilidad entre insumos y resultados, registrar decisiones metodológicas y documentar de manera reproducible cómo una combinación de fuentes heterogéneas se transforma en un dataset comunal consistente.

        El proyecto integra múltiples fuentes públicas porque ninguna de ellas contiene por sí sola la unidad analítica final requerida. La población comunal provee el denominador para indicadores por habitante, la pobreza por ingresos aporta una dimensión socioeconómica, las áreas verdes entregan una dimensión territorial y los ingresos propios permanentes aportan una aproximación a capacidad municipal. El valor del producto final no reside en inferir relaciones causales, sino en dejar una base integrada, consistente y consultable para describir desigualdades comunales observadas.
        """
    ).strip()


def build_section_02() -> str:
    return textwrap.dedent(
        """
        \\chapter{Objetivos}

        \\section{Objetivo general}

        Construir y documentar un proceso ETL reproducible que integre fuentes públicas sobre áreas verdes, pobreza por ingresos, capacidad municipal y población comunal, con el fin de generar un dataset final por comuna para la Provincia de Santiago y una base SQLite apta para consulta y análisis descriptivo.

        \\section{Objetivos específicos}

        \\begin{itemize}
        \\item Verificar la estructura base del repositorio, las rutas críticas y el contrato operativo de lectura de las fuentes.
        \\item Perfilar las cuatro fuentes reales, identificar conflictos de estructura y registrar diferencias relevantes para la integración.
        \\item Validar la dimensión maestra de comunas y resolver la homologación reproducible con \\texttt{codigo\\_comuna} como llave principal.
        \\item Generar artefactos staging por fuente con selección de columnas, tipificación, filtrado territorial y estandarización comunal.
        \\item Integrar el dataset final comunal con métricas derivadas por habitante y años de referencia explícitos.
        \\item Validar formalmente el dataset final y cargarlo a una base SQLite con estructura consultable.
        \\item Producir rankings, cruces descriptivos y figuras analíticas reutilizables para comunicación de resultados.
        \\end{itemize}
        """
    ).strip()


def build_section_03(ctx: dict[str, object]) -> str:
    return textwrap.dedent(
        f"""
        \\chapter{{Alcance y Decisiones Metodológicas}}

        \\section{{Alcance analítico}}

        La implementación observada en el repositorio trabaja con una unidad de análisis comunal: una fila del dataset final corresponde a una comuna. El universo final se restringe a la Provincia de Santiago y se valida contra \\texttt{{data/raw/dim\\_comuna\\_base.csv}}, que contiene 32 comunas. El producto integrado resultante mantiene esa cobertura sin faltantes ni extras.

        El análisis tiene naturaleza comparativa y descriptiva. En consecuencia, los outputs de Fase 9 se interpretan como patrones observados entre comunas y no como evidencia para inferir relaciones causales. Este criterio aparece de manera consistente en la documentación del repositorio y en los reportes analíticos.

        \\section{{Corte temporal y consistencia de referencia}}

        El proyecto no fuerza una homogeneización artificial de años entre fuentes. En el dataset final quedan registrados explícitamente \\texttt{{anio\\_poblacion = 2024}}, \\texttt{{anio\\_pobreza = 2022}}, \\texttt{{anio\\_areas\\_verdes = 2024}} y \\texttt{{anio\\_ingresos = 2024}}. Esta decisión preserva trazabilidad respecto del origen de cada variable y evita ocultar diferencias temporales entre insumos.

        \\section{{Llave principal y producto final}}

        La llave principal obligatoria del proyecto es \\texttt{{codigo\\_comuna}}. \\texttt{{nombre\\_comuna}} se mantiene como apoyo descriptivo y de verificación, pero no se usa como llave de integración. El producto final observado se compone de un CSV integrado con {ctx["dataset_rows"]} filas y {ctx["dataset_cols"]} columnas, una base SQLite con tres tablas y un conjunto de outputs de validación y análisis exploratorio.

        \\section{{Síntesis de decisiones}}

        \\input{{Tablas/tabla_decisiones_metodologicas.tex}}
        """
    ).strip()


def build_section_04() -> str:
    return textwrap.dedent(
        """
        \\chapter{Descripción de Fuentes}

        Las fuentes primarias del proyecto se documentan en \\texttt{data/raw/metadata\\_fuentes.csv}, archivo que opera como contrato de lectura para fases posteriores. Sobre esa base se distinguen cuatro insumos oficiales y versionados dentro del repositorio.

        \\input{Tablas/tabla_fuentes.tex}

        \\section{SINIM - Áreas verdes}

        Esta fuente se almacena en \\texttt{data/raw/datos\\_municipales\\_20260402222841\\_Sin-Corrección-Monetaria.xls}. Aunque usa extensión \\texttt{.xls}, la metadata y el código de extracción la tratan como SpreadsheetML/XML 2003. El archivo se lee en la hoja \\texttt{Hoja1} con \\texttt{skiprows = 2}. Su variable principal no está disponible como columna única de salida; el valor final \\texttt{areas\\_verdes\\_m2} se construye combinando \\texttt{mmpqc\\_2024} y \\texttt{mmpzc\\_2024}.

        \\section{SINIM - Capacidad municipal}

        La fuente de capacidad municipal se almacena en \\texttt{data/raw/datos\\_municipales\\_20260402223904\\_Sin-Corrección-Monetaria.xls}. Al igual que la fuente anterior, se lee como SpreadsheetML/XML 2003 desde \\texttt{Hoja1} con \\texttt{skiprows = 2}. La variable comunal utilizada es \\texttt{iadm41\\_2024}, que luego se renombra a \\texttt{ipp\\_miles\\_pesos} y se conserva en miles de pesos nominales 2024.

        \\section{Observatorio Social - Pobreza por ingresos}

        La fuente de pobreza corresponde a \\texttt{data/raw/estimaciones\\_tasa\\_pobreza\\_ingresos\\_comunas\\_2022.xlsx}. La metadata registra lectura directa con \\texttt{pandas.read\\_excel()}, hoja \\texttt{Estimaciones} y \\texttt{skiprows = 2}. La columna utilizada es \\texttt{Porcentaje de personas en situación de pobreza por ingresos 2022}. La propia metadata advierte que esta variable viene en escala 0--1, por lo que en transformación se convierte a porcentaje 0--100.

        \\section{Censo 2024 - Población comunal}

        La población comunal se toma desde \\texttt{data/raw/D1\\_Poblacion-censada-por-sexo-y-edad-en-grupos-quinquenales.xlsx}. La hoja operativa es \\texttt{2} con \\texttt{skiprows = 3}. Aunque la fuente incluye columnas adicionales de sexo y razón hombre-mujer, en esta fase solo se conserva \\texttt{Población censada}, ya que el objetivo del ETL es disponer de un denominador comunal consistente para indicadores por habitante.
        """
    ).strip()


def build_section_05() -> str:
    return textwrap.dedent(
        """
        \\chapter{Perfilado y Diagnóstico de Datos}

        El perfilado real de las fuentes quedó registrado en \\texttt{outputs/perfilado\\_fuentes.xlsx}, con una hoja \\texttt{resumen} y una hoja \\texttt{columnas}. Ese workbook, complementado por \\texttt{outputs/conflictos\\_fuentes.md}, permite documentar estructura, problemas de calidad y conflictos de integración antes de cualquier carga a staging.

        \\section{Estructura observada}

        Las fuentes A y B presentan 52 filas con 4 y 3 columnas útiles, respectivamente. Las fuentes C y D contienen 351 y 349 filas, con 10 columnas cada una en la lectura inicial. En las cuatro fuentes no se detectaron filas duplicadas completas durante el perfilado, pero sí diferencias importantes de alcance territorial y de estructura de encabezado.

        \\input{Tablas/tabla_perfilado_resumen.tex}

        \\section{Problemas de calidad y heterogeneidad}

        El diagnóstico registra cuatro grupos de problemas relevantes. Primero, las dos fuentes SINIM requieren parser especial porque el archivo corresponde a SpreadsheetML/XML 2003 y trae encabezados extendidos previos a la tabla útil. Segundo, todas las fuentes exceden el universo final de la Provincia de Santiago, por lo que debieron filtrarse contra la dimensión maestra comunal. Tercero, los nombres de comuna difieren de la base maestra por tildes, mayúsculas y escritura capitalizada. Cuarto, algunas variables exigieron limpieza o reinterpretación semántica antes de integrarse.

        En la fuente de áreas verdes se detectaron valores especiales \\texttt{No Aplica} y \\texttt{No Recepcionado}. En pobreza se identificaron seis filas de nota o blanco y una variable reportada originalmente como proporción 0--1. En población se identificaron dos filas no comunales y una fila agregada \\texttt{País}, que no corresponde a la unidad analítica final.

        \\section{Conflictos de integración}

        \\input{Tablas/tabla_conflictos_integracion.tex}

        El detalle fino de columnas, tipos, nulos y muestras textuales queda respaldado por el workbook de perfilado y no se replica completo en el cuerpo principal del informe para evitar redundancia. Ese detalle se remite a anexos y a los outputs técnicos del repositorio.
        """
    ).strip()


def build_section_06() -> str:
    return textwrap.dedent(
        """
        \\chapter{Estandarización de la Llave Maestra Comunal}

        \\section{Criterio de llave principal}

        El proyecto resuelve la integración por \\texttt{codigo\\_comuna}. Esta decisión se sustenta en evidencia directa de las fuentes: los nombres de comuna cambian entre escritura completamente en mayúsculas, escritura capitalizada y variantes con o sin tildes. Por esa razón, \\texttt{nombre\\_comuna} se mantiene como apoyo descriptivo y de verificación, pero no como llave de merge.

        \\section{Base maestra y universo final}

        La base maestra se encuentra en \\texttt{data/raw/dim\\_comuna\\_base.csv}. El reporte de homologación confirma 32 filas, unicidad de \\texttt{codigo\\_comuna} y \\texttt{nombre\\_comuna}, provincia única \\texttt{SANTIAGO} y región única \\texttt{METROPOLITANA DE SANTIAGO}. Ese archivo define el universo final del proyecto y se utiliza para acotar cobertura durante transformación e integración.

        \\section{Resultados de homologación}

        Dentro del universo final, las fuentes A y B presentan 26 coincidencias exactas y 6 coincidencias resueltas por normalización. Las fuentes C y D presentan 32 coincidencias resueltas por normalización y no dejan pendientes manuales para las comunas de interés. En todos los casos, el criterio operativo es filtrar por \\texttt{codigo\\_comuna} y luego sobreescribir \\texttt{nombre\\_comuna} con la versión estandarizada de la dimensión maestra.

        \\input{Tablas/tabla_homologacion_resumen_fuente.tex}

        \\section{Ejemplos reales}

        \\input{Tablas/tabla_homologacion_ejemplos.tex}

        \\section{Controles de unicidad y cobertura}

        La homologación no deja casos pendientes dentro de las 32 comunas del proyecto. El dataset final validado conserva una sola fila por \\texttt{codigo\\_comuna}, sin faltantes ni extras respecto a \\texttt{dim\\_comuna\\_base.csv}. Esta consistencia se vuelve a confirmar en la validación final y en la carga a SQLite.
        """
    ).strip()


def build_section_07(ctx: dict[str, object]) -> str:
    sqlite_counts: dict[str, int] = ctx["sqlite_counts"]  # type: ignore[assignment]
    return textwrap.dedent(
        f"""
        \\chapter{{Modelo de Datos}}

        Esta sección describe el modelo tal como existe en \\texttt{{db/lab1\\_desigualdad.sqlite}}. No se corrige ni reinterpreta el diseño observado; se documenta su implementación real. El modelo responde a una lógica dimensión-hecho complementada por una tabla de metadata.

        \\input{{Tablas/tabla_modelo_datos.tex}}

        \\section{{Tabla \\texttt{{dim\\_comuna}}}}

        La dimensión comunal contiene {sqlite_counts["dim_comuna"]} filas y cinco columnas: \\texttt{{codigo\\_comuna}}, \\texttt{{nombre\\_comuna}}, \\texttt{{provincia}}, \\texttt{{region}} y \\texttt{{fuente\\_referencia}}. Esta tabla preserva la identificación y el contexto territorial del universo final.

        \\section{{Tabla \\texttt{{fact\\_desigualdad\\_comunal}}}}

        La tabla de hechos contiene {sqlite_counts["fact_desigualdad_comunal"]} filas y once columnas. Su llave es \\texttt{{codigo\\_comuna}} y almacena \\texttt{{poblacion}}, \\texttt{{anio\\_poblacion}}, \\texttt{{pobreza\\_ingresos\\_pct}}, \\texttt{{anio\\_pobreza}}, \\texttt{{areas\\_verdes\\_m2}}, \\texttt{{anio\\_areas\\_verdes}}, \\texttt{{ipp\\_miles\\_pesos}}, \\texttt{{anio\\_ingresos}}, \\texttt{{areas\\_verdes\\_m2\\_hab}} e \\texttt{{ipp\\_pesos\\_hab}}. El campo \\texttt{{nombre\\_comuna}} no se replica en esta tabla; se obtiene mediante unión con \\texttt{{dim\\_comuna}}.

        \\section{{Tabla \\texttt{{metadata\\_fuentes}}}}

        La tabla \\texttt{{metadata\\_fuentes}} contiene {sqlite_counts["metadata_fuentes"]} filas y trece columnas. Su función es conservar la trazabilidad operativa de las fuentes: institución, URL, fecha de descarga, formato, año de referencia, hoja, \\texttt{{skiprows}}, archivo lógico y observaciones. Esta tabla conecta el resultado analítico con el contrato de lectura real del ETL.

        \\section{{Relación entre tablas}}

        El vínculo entre la dimensión y la tabla de hechos se realiza por \\texttt{{codigo\\_comuna}}. En términos operativos, la combinación \\texttt{{dim\\_comuna}} + \\texttt{{fact\\_desigualdad\\_comunal}} reproduce el dataset final validado, mientras que \\texttt{{metadata\\_fuentes}} documenta el origen de los insumos y las reglas mínimas de lectura.
        """
    ).strip()


def build_section_08() -> str:
    return textwrap.dedent(
        """
        \\chapter{Mapa Lógico de Datos}

        El mapa lógico resume cómo los datos transitan desde archivos raw heterogéneos hasta variables finales listas para validación, persistencia y análisis. En este proyecto, la secuencia observable es: contrato de lectura en metadata, lectura real por fuente, staging por fuente, integración sobre dimensión maestra, métricas derivadas y persistencia final en CSV y SQLite.

        \\input{Tablas/tabla_mapa_logico_resumido.tex}

        El flujo anterior muestra dos criterios centrales. Primero, las variables finales solo se construyen a partir de campos realmente presentes en las fuentes y en los artefactos staging. Segundo, cualquier transformación semántica relevante queda documentada en el código y en los reportes de salida, por ejemplo la conversión de pobreza desde proporción a porcentaje o la suma de componentes de áreas verdes para producir \\texttt{areas\\_verdes\\_m2}.

        El detalle extendido de artefactos y destinos se deja en anexos para facilitar trazabilidad técnica sin sobrecargar el cuerpo principal del informe.
        """
    ).strip()


def build_section_09() -> str:
    return textwrap.dedent(
        """
        \\chapter{Desarrollo del ETL}

        \\section{Extracción}

        La extracción se coordina desde \\texttt{src/main.py} y \\texttt{src/extract.py}. El proceso usa \\texttt{data/raw/metadata\\_fuentes.csv} como contrato operativo para ubicar archivo, hoja, \\texttt{skiprows}, formato y observaciones por fuente. Las fuentes A y B se leen mediante un parser específico para SpreadsheetML/XML 2003, mientras que las fuentes C y D se leen con \\texttt{pandas.read\\_excel()} respetando la configuración registrada en metadata.

        El resultado de esta etapa no es solo la lectura en memoria, sino también la generación de evidencia diagnóstica en \\texttt{outputs/perfilado\\_fuentes.xlsx} y \\texttt{outputs/conflictos\\_fuentes.md}. Esto permite detectar estructura real, filas fuera de alcance, valores especiales y heterogeneidad en nombres comunales antes de construir los staging.

        \\section{Transformación}

        La transformación se implementa en \\texttt{src/transform.py}. Cada fuente produce un staging independiente y validado. Las reglas aplicadas incluyen selección de columnas, renombre semántico, tipificación, formateo de \\texttt{codigo\\_comuna}, estandarización de \\texttt{nombre\\_comuna}, tratamiento de valores especiales, filtrado al universo final de 32 comunas y validaciones de rango.

        \\input{Tablas/tabla_transformaciones.tex}

        \\section{Integración}

        La integración se implementa en \\texttt{src/integrate.py}. El proceso parte desde \\texttt{dim\\_comuna\\_base.csv} y ejecuta cuatro merges \\texttt{left} con validación \\texttt{one\\_to\\_one}, en el orden población, pobreza, áreas verdes y capacidad municipal. Después del merge se asignan los años de referencia por variable y se calculan las métricas derivadas \\texttt{areas\\_verdes\\_m2\\_hab} e \\texttt{ipp\\_pesos\\_hab}, controlando divisiones inválidas e infinitos.

        El flujo completo puede reejecutarse desde la raíz del repositorio con \\texttt{python src/main.py} o \\texttt{python -m src.main}. Los reportes \\texttt{outputs/log\\_integracion.md}, \\texttt{outputs/resumen\\_dataset\\_final.md} y \\texttt{outputs/reporte\\_correcciones\\_pre\\_fase10.md} respaldan tanto la lógica del merge como la reproducibilidad observada del pipeline.
        """
    ).strip()


def build_section_10(ctx: dict[str, object]) -> str:
    dataset_rows = ctx["dataset_rows"]
    dataset_cols = ctx["dataset_cols"]
    return textwrap.dedent(
        f"""
        \\chapter{{Validación del Dataset Final}}

        La validación formal del dataset final quedó documentada en \\texttt{{outputs/reporte\\_validacion\\_final.csv}} y \\texttt{{outputs/reporte\\_validacion\\_final.md}}. El archivo validado es \\texttt{{data/processed/desigualdad\\_comunal\\_final.csv}}, con {dataset_rows} filas y {dataset_cols} columnas.

        \\input{{Tablas/tabla_validacion_resumen.tex}}

        Los chequeos reportados confirman una fila por comuna, unicidad de \\texttt{{codigo\\_comuna}}, formato de llave consistente de cinco dígitos, cobertura exacta respecto de la dimensión maestra y coincidencia de \\texttt{{nombre\\_comuna}} con \\texttt{{dim\\_comuna\\_base.csv}}. También se informa convertibilidad numérica sin errores para todas las columnas cuantitativas, nulos igual a cero en las doce columnas finales y años de referencia consistentes con la fase de integración.

        Desde el punto de vista de reglas de negocio mínimas, la validación confirma \\texttt{{poblacion > 0}}, \\texttt{{pobreza\\_ingresos\\_pct}} entre 0 y 100, ausencia de áreas verdes negativas, ausencia de IPP negativos y ausencia de infinitos en las métricas derivadas por habitante. Sobre esa base, el propio reporte marca el dataset como apto para la fase de carga a SQLite.
        """
    ).strip()


def build_section_11(ctx: dict[str, object]) -> str:
    sqlite_counts: dict[str, int] = ctx["sqlite_counts"]  # type: ignore[assignment]
    quick_check = ctx["sqlite_quick_check"]
    return textwrap.dedent(
        f"""
        \\chapter{{Carga Final a SQLite}}

        La persistencia final del proyecto se materializa en \\texttt{{db/lab1\\_desigualdad.sqlite}}. En términos operativos, esta elección deja un artefacto local único, consultable con SQL y suficiente para validar consistencia entre dimensión, tabla de hechos y metadata sin depender de un servidor externo.

        \\section{{Estructura y conteos}}

        La base resultante contiene las tablas \\texttt{{dim\\_comuna}}, \\texttt{{fact\\_desigualdad\\_comunal}} y \\texttt{{metadata\\_fuentes}}. El reporte de carga y la inspección directa de la base coinciden en los conteos observados.

        \\input{{Tablas/tabla_sqlite_conteos.tex}}

        \\section{{Integridad básica}}

        El archivo abre correctamente y el chequeo \\texttt{{PRAGMA quick\\_check}} devuelve \\texttt{{{quick_check}}}. Además, los reportes de carga informan ausencia de duplicados por \\texttt{{codigo\\_comuna}} en la dimensión y en la tabla de hechos, y ausencia de códigos huérfanos entre ambas tablas.

        \\section{{Consultas de prueba}}

        Las consultas documentadas tras la carga reproducen conteos por tabla y rankings básicos para áreas verdes, pobreza e IPP. Esto confirma que la base queda utilizable no solo como respaldo del dataset final, sino también como soporte de consulta analítica.

        \\input{{Tablas/tabla_sqlite_consultas_prueba.tex}}

        En síntesis, la carga final reproduce el resultado del ETL sin alterar la centralidad de \\texttt{{codigo\\_comuna}}. \\texttt{{dim\\_comuna}} conserva los descriptores territoriales, \\texttt{{fact\\_desigualdad\\_comunal}} concentra las variables finales cuantitativas y \\texttt{{metadata\\_fuentes}} mantiene la trazabilidad del proceso de lectura.
        """
    ).strip()


def build_section_12(ctx: dict[str, object]) -> str:
    top_areas = ctx["top_bottom_areas"]["nombre_comuna"].astype(str).tolist()  # type: ignore[index]
    top_pobreza = ctx["top_pobreza"]["nombre_comuna"].astype(str).tolist()  # type: ignore[index]
    top_ipp = ctx["top_ipp"]["nombre_comuna"].astype(str).tolist()  # type: ignore[index]
    peor_pobreza_areas = ctx["peor_pobreza_areas"]["nombre_comuna"].astype(str).tolist()  # type: ignore[index]
    peor_pobreza_ipp = ctx["peor_pobreza_ipp"]["nombre_comuna"].astype(str).tolist()  # type: ignore[index]
    rezagadas = ctx["rezagadas_multidim"]["nombre_comuna"].astype(str).tolist()  # type: ignore[index]
    quilicura_value = format_decimal(ctx["quilicura_row"]["areas_verdes_m2_hab"], 6)  # type: ignore[index]
    la_reina_value = format_decimal(ctx["la_reina_row"]["areas_verdes_m2_hab"], 6)  # type: ignore[index]
    providencia_value = format_decimal(ctx["providencia_row"]["areas_verdes_m2_hab"], 6)  # type: ignore[index]
    return textwrap.dedent(
        f"""
        \\chapter{{Resultados y Análisis Exploratorio}}

        Esta sección se apoya en \\texttt{{outputs/analisis\\_exploratorio.md}}, \\texttt{{outputs/tablas\\_hallazgos\\_fase9.csv}}, los rankings exportados y las figuras generadas en Fase 9. La lectura se mantiene en un plano estrictamente descriptivo.

        \\section{{Rankings por dimensión}}

        Los menores valores observados de \\texttt{{areas\\_verdes\\_m2\\_hab}} corresponden a {", ".join(top_areas)}. En pobreza por ingresos, los mayores valores observados corresponden a {", ".join(top_pobreza)}. En \\texttt{{ipp\\_pesos\\_hab}}, los menores valores observados corresponden a {", ".join(top_ipp)}.

        \\input{{Tablas/tabla_hallazgos_resumen.tex}}

        \\begin{{figure}}[htbp]
        \\centering
        \\includegraphics[width=0.88\\textwidth]{{Figuras/areas_verdes_m2_hab_bottom10.png}}
        \\caption{{Diez comunas con menor disponibilidad de áreas verdes por habitante.}}
        \\end{{figure}}

        \\begin{{figure}}[htbp]
        \\centering
        \\includegraphics[width=0.88\\textwidth]{{Figuras/pobreza_ingresos_top10.png}}
        \\caption{{Diez comunas con mayor pobreza por ingresos en el dataset final.}}
        \\end{{figure}}

        \\begin{{figure}}[htbp]
        \\centering
        \\includegraphics[width=0.88\\textwidth]{{Figuras/ipp_pesos_hab_bottom10.png}}
        \\caption{{Diez comunas con menor IPP por habitante en el dataset final.}}
        \\end{{figure}}

        \\section{{Cruces descriptivos y rezago en múltiples dimensiones}}

        El cruce por quintiles muestra que el peor quintil simultáneo de pobreza y áreas verdes por habitante se observa en {", ".join(peor_pobreza_areas)}. Por su parte, el peor quintil simultáneo de pobreza e IPP por habitante se observa en {", ".join(peor_pobreza_ipp)}. Al ampliar la mirada a rezago crítico en al menos dos dimensiones, aparecen {", ".join(rezagadas)}.

        El índice auxiliar de rezago territorial, definido en Fase 9 como suma de quintiles de rezago, ordena en los primeros lugares a Conchalí, El Bosque, Lo Espejo, La Pintana y San Ramón. Este índice se interpreta solo como apoyo descriptivo para resumir coincidencias de rezago relativo entre comunas.

        \\input{{Tablas/tabla_rezagadas_multidimensionales.tex}}

        \\begin{{figure}}[htbp]
        \\centering
        \\includegraphics[width=0.88\\textwidth]{{Figuras/indice_rezago_territorial_top10.png}}
        \\caption{{Diez comunas con mayor índice auxiliar de rezago territorial.}}
        \\end{{figure}}

        \\section{{Lectura descriptiva del scatter y tratamiento del outlier}}

        El scatter de pobreza y áreas verdes por habitante se mantiene como evidencia exploratoria y no como prueba de relación causal. Su lectura exige una advertencia metodológica explícita: Quilicura registra \\texttt{{areas\\_verdes\\_m2\\_hab = {quilicura_value}}}, muy por encima de La Reina ({la_reina_value}) y Providencia ({providencia_value}). Por esta razón, el gráfico fue documentado con escala logarítmica en el eje X para preservar visibilidad sobre el resto de las comunas.

        \\begin{{figure}}[htbp]
        \\centering
        \\includegraphics[width=0.88\\textwidth]{{Figuras/pobreza_vs_areas_verdes_scatter.png}}
        \\caption{{Scatter descriptivo entre pobreza por ingresos y áreas verdes por habitante.}}
        \\end{{figure}}

        En términos comunicacionales, el caso de Quilicura debe tratarse como outlier plausible y no como valor descartado. El repositorio no aporta evidencia para clasificarlo como error; por lo tanto, la decisión metodológica correcta es mantenerlo, advertir su influencia en la escala y evitar interpretaciones causales a partir del gráfico.
        """
    ).strip()


def build_section_13() -> str:
    return textwrap.dedent(
        """
        \\chapter{Limitaciones}

        El proyecto presenta limitaciones metodológicas que deben hacerse explícitas para interpretar correctamente el dataset y los outputs analíticos.

        \\begin{itemize}
        \\item Las fuentes no son perfectamente homogéneas en términos temporales: pobreza por ingresos corresponde a 2022, mientras población, áreas verdes e IPP corresponden a 2024.
        \\item El análisis es comparativo y descriptivo; no permite sostener inferencias causales entre pobreza, áreas verdes y capacidad municipal.
        \\item El \\texttt{indice\\_rezago\\_territorial} es una construcción auxiliar de Fase 9 y no una variable oficial provista por las instituciones fuente.
        \\item Existen outliers plausibles que afectan la lectura visual, en particular Quilicura en \\texttt{areas\\_verdes\\_m2\\_hab} y varias comunas de altos ingresos en \\texttt{ipp\\_pesos\\_hab}.
        \\item La interpretación depende de definiciones institucionales de origen, por ejemplo la forma en que cada fuente publica áreas verdes, IPP o pobreza por ingresos.
        \\item El universo analizado se restringe a la Provincia de Santiago, por lo que el dataset final no representa al total regional ni nacional.
        \\end{itemize}

        Estas limitaciones no invalidan el producto final, pero sí acotan su uso legítimo: comparación territorial observada, trazabilidad metodológica y reutilización del dataset integrado bajo el mismo marco descriptivo.
        """
    ).strip()


def build_section_14() -> str:
    return textwrap.dedent(
        """
        \\chapter{Conclusiones}

        Desde el punto de vista técnico, el repositorio documenta un proceso ETL cerrado y reproducible para integrar cuatro fuentes públicas heterogéneas bajo una llave comunal estable. La secuencia de perfilado, homologación, staging, integración, validación y carga final se encuentra respaldada por código fuente, reportes técnicos y artefactos exportados. El resultado es un dataset comunal consistente y una base SQLite consultable, sin necesidad de reinterpretar ni corregir el modelo observado.

        Desde el punto de vista analítico, los outputs de Fase 9 muestran que las dimensiones incluidas no se distribuyen homogéneamente entre comunas. Se observan grupos comunales recurrentes en posiciones de rezago relativo, tanto en rankings individuales como en cruces de pobreza con áreas verdes o con IPP por habitante. Estas observaciones deben mantenerse en clave descriptiva, sin extrapolar mecanismos causales.

        El valor principal del trabajo no se limita al informe. El CSV final y la base SQLite quedan disponibles como productos reutilizables para consultas, auditoría metodológica, análisis exploratorios posteriores y montaje del informe final en el template externo. En ese sentido, la Fase 10 preparada en este paquete no reemplaza el ETL, sino que lo traduce a materiales documentales trazables y listos para integración editorial.
        """
    ).strip()


def create_sections(ctx: dict[str, object]) -> None:
    write_text(DOCS_DIR / "Resumen.tex", build_resumen(ctx))
    sections = {
        "01_introduccion.tex": build_section_01(),
        "02_objetivos.tex": build_section_02(),
        "03_alcance_decisiones_metodologicas.tex": build_section_03(ctx),
        "04_fuentes.tex": build_section_04(),
        "05_perfilado_diagnostico.tex": build_section_05(),
        "06_llave_maestra.tex": build_section_06(),
        "07_modelo_datos.tex": build_section_07(ctx),
        "08_mapa_logico.tex": build_section_08(),
        "09_desarrollo_etl.tex": build_section_09(),
        "10_validacion_dataset.tex": build_section_10(ctx),
        "11_carga_sqlite.tex": build_section_11(ctx),
        "12_resultados_analisis.tex": build_section_12(ctx),
        "13_limitaciones.tex": build_section_13(),
        "14_conclusiones.tex": build_section_14(),
    }
    for filename, content in sections.items():
        write_text(SECCIONES_DIR / filename, content)


def create_anexos() -> None:
    content = textwrap.dedent(
        """
        \\appendix

        \\chapter{Diccionario de datos final}

        Este anexo resume las 12 variables que componen el dataset final integrado y deja explícito el origen de cada una.

        \\input{Tablas/tabla_diccionario_datos_final.tex}

        \\chapter{Perfilado extendido}

        El detalle extendido del perfilado se respalda en \\texttt{outputs/perfilado\\_fuentes.xlsx}. La siguiente tabla resume la estructura observada en la etapa diagnóstica.

        \\input{Tablas/tabla_perfilado_resumen.tex}

        \\chapter{Homologación de comunas}

        La homologación se resolvió sin pendientes manuales dentro del universo final. Se documentan a continuación el resumen por fuente y ejemplos de normalización aplicada.

        \\input{Tablas/tabla_homologacion_resumen_fuente.tex}

        \\input{Tablas/tabla_homologacion_ejemplos.tex}

        \\chapter{Mapa lógico extendido}

        Este anexo deja trazabilidad entre artefactos del ETL y sus destinos operativos.

        \\input{Tablas/tabla_mapa_logico_extendido.tex}

        \\chapter{Validación final del dataset}

        La validación de Fase 7 confirma consistencia estructural, cobertura y rangos.

        \\input{Tablas/tabla_validacion_resumen.tex}

        \\chapter{Carga SQLite}

        Se resumen los conteos observados y las consultas de prueba utilizadas tras la carga final.

        \\input{Tablas/tabla_sqlite_conteos.tex}

        \\input{Tablas/tabla_sqlite_consultas_prueba.tex}

        \\chapter{Revisión breve de Fase 9: outliers y comunicabilidad}

        La revisión corta de Fase 9 respalda tres advertencias: el índice de rezago es auxiliar, Quilicura debe tratarse como outlier plausible en áreas verdes por habitante y el scatter requiere lectura cuidadosa por su escala. Para el informe final conviene mantener estas advertencias junto a las figuras analíticas.

        \\input{Tablas/tabla_hallazgos_resumen.tex}
        """
    ).strip()
    write_text(ANEXOS_DIR / "anexos.tex", content)


def create_validation_sandbox() -> dict[str, object]:
    main_sandbox = textwrap.dedent(
        """
        \\documentclass[12pt]{report}
        \\usepackage[utf8]{inputenc}
        \\usepackage[T1]{fontenc}
        \\usepackage[spanish,es-nodecimaldot]{babel}
        \\usepackage{graphicx}
        \\usepackage{float}
        \\usepackage{geometry}
        \\geometry{margin=2.5cm}
        \\makeatletter
        \\def\\input@path{{../}}
        \\makeatother
        \\graphicspath{{../}}
        \\begin{document}
        \\input{Resumen}
        \\input{Secciones/01_introduccion}
        \\input{Secciones/02_objetivos}
        \\input{Secciones/03_alcance_decisiones_metodologicas}
        \\input{Secciones/04_fuentes}
        \\input{Secciones/05_perfilado_diagnostico}
        \\input{Secciones/06_llave_maestra}
        \\input{Secciones/07_modelo_datos}
        \\input{Secciones/08_mapa_logico}
        \\input{Secciones/09_desarrollo_etl}
        \\input{Secciones/10_validacion_dataset}
        \\input{Secciones/11_carga_sqlite}
        \\input{Secciones/12_resultados_analisis}
        \\input{Secciones/13_limitaciones}
        \\input{Secciones/14_conclusiones}
        \\input{Anexos/anexos}
        \\end{document}
        """
    ).strip()
    write_text(VALIDACION_DIR / "main_sandbox.tex", main_sandbox)
    for suffix in (".aux", ".log", ".pdf", ".out", ".toc"):
        candidate = VALIDACION_DIR / f"main_sandbox{suffix}"
        if candidate.exists():
            candidate.unlink()

    pdflatex = shutil.which("pdflatex")
    result = {
        "available": bool(pdflatex),
        "success": False,
        "stdout": "",
        "stderr": "",
        "returncode": None,
    }
    if not pdflatex:
        write_text(
            VALIDACION_DIR / "resultado_validacion.md",
            "# Validación LaTeX mínima\n\nNo se encontró `pdflatex` en el entorno; no fue posible compilar el sandbox.\n",
        )
        return result

    completed = subprocess.run(
        [
            pdflatex,
            "-interaction=nonstopmode",
            "-halt-on-error",
            "main_sandbox.tex",
        ],
        cwd=VALIDACION_DIR,
        capture_output=True,
    )
    stdout_text = completed.stdout.decode("utf-8", errors="replace")
    stderr_text = completed.stderr.decode("utf-8", errors="replace")
    result.update(
        {
            "success": completed.returncode == 0,
            "stdout": stdout_text,
            "stderr": stderr_text,
            "returncode": completed.returncode,
        }
    )
    status = "OK" if completed.returncode == 0 else "ERROR"
    body = textwrap.dedent(
        f"# Validación LaTeX mínima\n\n"
        f"- Herramienta detectada: `pdflatex`\n"
        f"- Archivo compilado: `_validacion/main_sandbox.tex`\n"
        f"- Resultado: `{status}`\n"
        f"- Código de salida: `{completed.returncode}`\n\n"
        "## Salida relevante\n\n"
        "```text\n"
        f"{stdout_text[-4000:]}\n"
        "```"
    ).strip()
    if stderr_text.strip():
        body += "\n\n## stderr\n\n```text\n" + stderr_text[-4000:] + "\n```\n"
    write_text(VALIDACION_DIR / "resultado_validacion.md", body)
    return result


def create_report(ctx: dict[str, object], latex_validation: dict[str, object]) -> None:
    outputs_presence: dict[str, bool] = ctx["outputs_presence"]  # type: ignore[assignment]
    sqlite_counts: dict[str, int] = ctx["sqlite_counts"]  # type: ignore[assignment]
    dataset_rows = ctx["dataset_rows"]
    dataset_cols = ctx["dataset_cols"]
    duplicated_codes = ctx["duplicated_codes"]
    missing_outputs = [path for path, exists in outputs_presence.items() if not exists]
    created_files = sorted(
        str(path.relative_to(ROOT))
        for path in DOCS_DIR.rglob("*")
        if path.is_file()
    )
    validation_lines = [
        f"- Dataset final: {dataset_rows} filas, {dataset_cols} columnas, duplicados por codigo_comuna = {duplicated_codes}.",
        (
            "- SQLite: tablas "
            f"{', '.join(ctx['sqlite_tables'])}; conteos dim/fact/metadata = "
            f"{sqlite_counts['dim_comuna']}/{sqlite_counts['fact_desigualdad_comunal']}/{sqlite_counts['metadata_fuentes']}."
        ),
        (
            "- Outputs clave Fases 7-9: "
            + ("todos presentes." if not missing_outputs else f"faltantes={missing_outputs}.")
        ),
    ]
    if latex_validation["available"]:
        validation_lines.append(
            f"- Validación LaTeX mínima: {'OK' if latex_validation['success'] else 'ERROR'} "
            f"(código de salida {latex_validation['returncode']})."
        )
    else:
        validation_lines.append("- Validación LaTeX mínima: no ejecutada por ausencia de `pdflatex` en el entorno.")

    report = textwrap.dedent(
        f"# Reporte de preparación Fase 10\n\n"
        "## 1. Resumen ejecutivo breve\n\n"
        "Se generó un paquete autocontenido en `docs/informe_lab1_materiales/` con fragmentos LaTeX para `Resumen.tex`, secciones 01-14, anexos, tablas auxiliares, manifiesto de figuras, referencias bibliográficas, trazabilidad del informe y reporte de preparación. El contenido quedó listo para ser copiado a un template externo manteniendo la estructura relativa de carpetas.\n\n"
        "Quedó listo para traspaso al template:\n\n"
        "- contenido redactado en español y basado en evidencia real del repo;\n"
        "- tablas `.tex` listas para `\\input{}`;\n"
        "- copias de las figuras analíticas clave;\n"
        "- `referencias_lab1.bib` construido con metadata real;\n"
        "- `trazabilidad_informe.csv` para auditoría de afirmaciones;\n"
        "- sandbox de validación LaTeX mínima.\n\n"
        "Pendiente para el paso de integración al template:\n\n"
        "- completar autores, docente, carrera y fecha en el archivo de metadatos del template;\n"
        "- insertar estos fragmentos en `informe-lab1` y ajustar, si fuera necesario, solo detalles editoriales del template.\n\n"
        "## 2. Auditoría inicial\n\n"
        "Se verificó la estructura principal del repo, la existencia de `data/processed/desigualdad_comunal_final.csv`, `db/lab1_desigualdad.sqlite` y los outputs clave de Fases 2 a 9. También se contrastó el dataset final con la base SQLite y se revisaron los reportes de transformaciones, integración, validación y análisis exploratorio.\n\n"
        "Hallazgos de auditoría:\n\n"
        f"- dataset final observado: {dataset_rows} filas, {dataset_cols} columnas, una fila por comuna y sin duplicados por `codigo_comuna`;\n"
        f"- SQLite observada: tablas `dim_comuna`, `fact_desigualdad_comunal`, `metadata_fuentes` con conteos {sqlite_counts['dim_comuna']} / {sqlite_counts['fact_desigualdad_comunal']} / {sqlite_counts['metadata_fuentes']};\n"
        "- outputs de validación, carga y análisis presentes y coherentes con el dataset final;\n"
        "- no se detectaron inconsistencias entre el estado esperado para Fases 1 a 9 y la evidencia real del repositorio.\n\n"
        "## 3. Archivos creados\n\n"
        f"{chr(10).join(f'- `{path}`' for path in created_files)}\n\n"
        "## 4. Evidencia usada\n\n"
        "Principales archivos fuente utilizados:\n\n"
        "- `data/raw/metadata_fuentes.csv`\n"
        "- `data/raw/dim_comuna_base.csv`\n"
        "- `data/processed/desigualdad_comunal_final.csv`\n"
        "- `db/lab1_desigualdad.sqlite`\n"
        "- `src/config.py`, `src/extract.py`, `src/comunas.py`, `src/transform.py`, `src/integrate.py`, `src/validate.py`, `src/load.py`, `src/analyze.py`, `src/main.py`\n"
        "- `outputs/perfilado_fuentes.xlsx`\n"
        "- `outputs/conflictos_fuentes.md`\n"
        "- `outputs/homologacion_comunas.csv`\n"
        "- `outputs/resumen_homologacion.md`\n"
        "- `outputs/resumen_transformaciones.md`\n"
        "- `outputs/validacion_staging.csv`\n"
        "- `outputs/log_integracion.md`\n"
        "- `outputs/resumen_dataset_final.md`\n"
        "- `outputs/reporte_validacion_final.csv`\n"
        "- `outputs/reporte_validacion_final.md`\n"
        "- `outputs/reporte_carga_sqlite.md`\n"
        "- `outputs/reporte_consultas_sqlite.csv`\n"
        "- `outputs/analisis_exploratorio.md`\n"
        "- `outputs/tablas_hallazgos_fase9.csv`\n"
        "- rankings y figuras de `outputs/`\n\n"
        "## 5. Validaciones\n\n"
        f"{chr(10).join(validation_lines)}\n\n"
        "## 6. Riesgos o pendientes residuales\n\n"
        "- `00_metadatos_sugeridos.md` deja como `TODO` los campos de carrera, docente, autores y fecha porque esos insumos no fueron encontrados dentro del repo.\n"
        "- La integración al template externo puede requerir ajustes editoriales menores del template, pero no de contenido factual.\n"
        "- Las figuras se copiaron sin alteración visual; el tratamiento del outlier de Quilicura quedó documentado solo como advertencia metodológica.\n"
    ).strip()
    write_text(DOCS_DIR / "reporte_preparacion_fase10.md", report)


def main() -> int:
    ensure_dirs()
    ctx = build_context()
    create_tables(ctx)
    copy_figures()
    create_manifest_figuras(ctx)
    create_metadatos()
    create_readme_handoff()
    create_referencias(ctx)
    create_traceability()
    create_sections(ctx)
    create_anexos()
    latex_validation = create_validation_sandbox()
    create_report(ctx, latex_validation)
    print(f"Materiales generados en {relpath(DOCS_DIR)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
