from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from config import (
    BASE_DIR,
    DIM_COMUNA_BASE_PATH,
    EXPECTED_DIM_COMUNA_ROWS,
    FINAL_DATASET_PATH,
    LOG_INTEGRACION_PATH,
    RESUMEN_DATASET_FINAL_PATH,
    STAGING_SOURCE_PATHS,
    ensure_directories,
)

REFERENCE_YEARS = {
    "anio_poblacion": 2024,
    "anio_pobreza": 2022,
    "anio_areas_verdes": 2024,
    "anio_ingresos": 2024,
}

FINAL_DATASET_COLUMNS = (
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
)

STAGING_CONTRACTS = {
    "D": {
        "label": "Poblacion comunal",
        "path": STAGING_SOURCE_PATHS["D"],
        "expected_columns": (
            "codigo_comuna",
            "nombre_comuna",
            "poblacion",
        ),
        "merge_columns": ("poblacion",),
        "numeric_types": {"poblacion": "Int64"},
        "year_column": "anio_poblacion",
    },
    "C": {
        "label": "Pobreza por ingresos",
        "path": STAGING_SOURCE_PATHS["C"],
        "expected_columns": (
            "codigo_comuna",
            "nombre_comuna",
            "pobreza_ingresos_pct",
        ),
        "merge_columns": ("pobreza_ingresos_pct",),
        "numeric_types": {"pobreza_ingresos_pct": "Float64"},
        "year_column": "anio_pobreza",
    },
    "A": {
        "label": "Areas verdes",
        "path": STAGING_SOURCE_PATHS["A"],
        "expected_columns": (
            "codigo_comuna",
            "nombre_comuna",
            "mmpqc_2024",
            "mmpzc_2024",
            "areas_verdes_m2",
        ),
        "merge_columns": ("areas_verdes_m2",),
        "numeric_types": {
            "mmpqc_2024": "Int64",
            "mmpzc_2024": "Int64",
            "areas_verdes_m2": "Int64",
        },
        "year_column": "anio_areas_verdes",
    },
    "B": {
        "label": "Capacidad municipal",
        "path": STAGING_SOURCE_PATHS["B"],
        "expected_columns": (
            "codigo_comuna",
            "nombre_comuna",
            "ipp_miles_pesos",
        ),
        "merge_columns": ("ipp_miles_pesos",),
        "numeric_types": {"ipp_miles_pesos": "Int64"},
        "year_column": "anio_ingresos",
    },
}

INTEGRATION_SEQUENCE = ("D", "C", "A", "B")
VARIABLE_DEFINITIONS = {
    "codigo_comuna": "Llave maestra comunal oficial del proyecto.",
    "nombre_comuna": "Nombre oficial de la comuna segun `dim_comuna_base.csv`.",
    "poblacion": "Poblacion comunal censada usada para el denominador de indicadores por habitante.",
    "anio_poblacion": "Anio de referencia de la poblacion comunal.",
    "pobreza_ingresos_pct": "Porcentaje de personas en situacion de pobreza por ingresos.",
    "anio_pobreza": "Anio de referencia de la pobreza por ingresos.",
    "areas_verdes_m2": "Superficie total de areas verdes comunales en metros cuadrados.",
    "anio_areas_verdes": "Anio de referencia de las areas verdes.",
    "ipp_miles_pesos": "Ingresos propios permanentes comunales en miles de pesos nominales.",
    "anio_ingresos": "Anio de referencia del IPP.",
    "areas_verdes_m2_hab": (
        "Metricas derivada: `areas_verdes_m2 / poblacion`. "
        "Se deja `NaN` si falta algun dato o si `poblacion <= 0`."
    ),
    "ipp_pesos_hab": (
        "Metrica derivada: `(ipp_miles_pesos * 1000) / poblacion`. "
        "Se deja `NaN` si falta algun dato o si `poblacion <= 0`."
    ),
}


@dataclass(frozen=True)
class IntegrationStepEvidence:
    source_id: str
    source_label: str
    staging_path: str
    rows_before: int
    rows_after: int
    added_columns: tuple[str, ...]
    null_counts: dict[str, int]
    source_duplicates: int
    result_duplicates: int
    unmatched_rows: int


def _relpath(path: Path) -> str:
    return path.relative_to(BASE_DIR).as_posix()


def _format_codigo_comuna(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce").astype("Int64")
    return numeric.map(
        lambda value: f"{int(value):05d}" if pd.notna(value) else pd.NA
    ).astype("string")


def _load_master_dimension(path: Path = DIM_COMUNA_BASE_PATH) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"No existe la base maestra: {_relpath(path)}")

    dim_base = pd.read_csv(path, dtype={"codigo_comuna": "string"})
    required_columns = ("codigo_comuna", "nombre_comuna")
    if tuple(map(str, dim_base.columns[:2]))[:2] != required_columns:
        missing = [column for column in required_columns if column not in dim_base.columns]
        if missing:
            raise ValueError(
                "La base maestra no contiene las columnas minimas requeridas: "
                f"{', '.join(missing)}."
            )

    dim_base["codigo_comuna"] = _format_codigo_comuna(dim_base["codigo_comuna"])
    dim_base = dim_base[["codigo_comuna", "nombre_comuna"]].copy()

    if len(dim_base) != EXPECTED_DIM_COMUNA_ROWS:
        raise ValueError(
            "La base maestra debe tener 32 comunas antes de integrar y hoy tiene "
            f"{len(dim_base)}."
        )
    if int(dim_base["codigo_comuna"].isna().sum()) != 0:
        raise ValueError("La base maestra tiene `codigo_comuna` nulo.")
    if int(dim_base["codigo_comuna"].duplicated().sum()) != 0:
        raise ValueError("La base maestra tiene duplicados por `codigo_comuna`.")

    return dim_base


def load_staging_sources() -> dict[str, pd.DataFrame]:
    staging_tables: dict[str, pd.DataFrame] = {}
    for source_id in INTEGRATION_SEQUENCE:
        contract = STAGING_CONTRACTS[source_id]
        path = contract["path"]
        if not path.exists():
            raise FileNotFoundError(f"No existe el staging requerido: {_relpath(path)}")

        dataframe = pd.read_csv(path, dtype={"codigo_comuna": "string"})
        actual_columns = tuple(map(str, dataframe.columns))
        if actual_columns != contract["expected_columns"]:
            raise ValueError(
                f"El staging {path.name} no coincide con el contrato esperado. "
                f"Esperado={contract['expected_columns']}; observado={actual_columns}."
            )

        dataframe["codigo_comuna"] = _format_codigo_comuna(dataframe["codigo_comuna"])
        for column, dtype in contract["numeric_types"].items():
            dataframe[column] = pd.to_numeric(dataframe[column], errors="coerce").astype(dtype)

        if len(dataframe) != EXPECTED_DIM_COMUNA_ROWS:
            raise ValueError(
                f"El staging {path.name} tiene {len(dataframe)} filas; se esperaban "
                f"{EXPECTED_DIM_COMUNA_ROWS}."
            )
        if int(dataframe["codigo_comuna"].isna().sum()) != 0:
            raise ValueError(f"El staging {path.name} tiene `codigo_comuna` nulo.")
        if int(dataframe["codigo_comuna"].duplicated().sum()) != 0:
            raise ValueError(f"El staging {path.name} tiene duplicados por `codigo_comuna`.")

        staging_tables[source_id] = dataframe

    return staging_tables


def _merge_source(
    base_df: pd.DataFrame,
    source_id: str,
    source_df: pd.DataFrame,
) -> tuple[pd.DataFrame, IntegrationStepEvidence]:
    contract = STAGING_CONTRACTS[source_id]
    merge_columns = list(contract["merge_columns"])
    year_column = str(contract["year_column"])
    rows_before = len(base_df)
    source_duplicates = int(source_df["codigo_comuna"].duplicated().sum())
    if source_duplicates != 0:
        raise ValueError(
            f"El staging {_relpath(contract['path'])} no es apto para merge: "
            f"duplicados por `codigo_comuna`={source_duplicates}."
        )

    payload = source_df[["codigo_comuna", *merge_columns]].copy()
    try:
        merged = base_df.merge(
            payload,
            on="codigo_comuna",
            how="left",
            validate="one_to_one",
            sort=False,
        )
    except pd.errors.MergeError as exc:
        raise ValueError(
            f"Fallo el merge con {contract['label']} por cardinalidad invalida."
        ) from exc

    rows_after = len(merged)
    if rows_after != rows_before:
        raise ValueError(
            f"El merge con {contract['label']} altero la cantidad de filas: "
            f"{rows_before} -> {rows_after}."
        )
    if rows_after != EXPECTED_DIM_COMUNA_ROWS:
        raise ValueError(
            f"La integracion quedo con {rows_after} filas; se esperaban "
            f"{EXPECTED_DIM_COMUNA_ROWS}."
        )

    missing_codes = sorted(set(base_df["codigo_comuna"]) - set(merged["codigo_comuna"]))
    if missing_codes:
        raise ValueError(
            "Se perdieron comunas durante el merge con "
            f"{contract['label']}: {missing_codes}."
        )

    result_duplicates = int(merged["codigo_comuna"].duplicated().sum())
    if result_duplicates != 0:
        raise ValueError(
            f"El resultado del merge con {contract['label']} quedo con duplicados por "
            "`codigo_comuna`."
        )

    merged[year_column] = REFERENCE_YEARS[year_column]
    null_counts = {column: int(merged[column].isna().sum()) for column in merge_columns}
    unmatched_rows = int(merged[merge_columns].isna().all(axis=1).sum())
    evidence = IntegrationStepEvidence(
        source_id=source_id,
        source_label=str(contract["label"]),
        staging_path=_relpath(contract["path"]),
        rows_before=rows_before,
        rows_after=rows_after,
        added_columns=tuple((*merge_columns, year_column)),
        null_counts=null_counts,
        source_duplicates=source_duplicates,
        result_duplicates=result_duplicates,
        unmatched_rows=unmatched_rows,
    )
    return merged, evidence


def create_derived_metrics(dataframe: pd.DataFrame) -> pd.DataFrame:
    final_df = dataframe.copy()
    for year_column, year_value in REFERENCE_YEARS.items():
        if year_column not in final_df.columns:
            final_df[year_column] = year_value

    population = pd.to_numeric(final_df["poblacion"], errors="coerce").astype("Float64")
    areas = pd.to_numeric(final_df["areas_verdes_m2"], errors="coerce").astype("Float64")
    ipp = pd.to_numeric(final_df["ipp_miles_pesos"], errors="coerce").astype("Float64")
    valid_population = population.notna() & population.gt(0)

    areas_per_capita = (areas / population).where(valid_population & areas.notna(), pd.NA)
    ipp_per_capita = ((ipp * 1000) / population).where(valid_population & ipp.notna(), pd.NA)

    final_df["areas_verdes_m2_hab"] = (
        areas_per_capita.replace([float("inf"), float("-inf")], pd.NA)
        .round(6)
        .astype("Float64")
    )
    final_df["ipp_pesos_hab"] = (
        ipp_per_capita.replace([float("inf"), float("-inf")], pd.NA)
        .round(6)
        .astype("Float64")
    )
    return final_df[list(FINAL_DATASET_COLUMNS)]


def _collect_final_validation(final_df: pd.DataFrame) -> dict[str, object]:
    numeric_checks = {
        "areas_verdes_m2_hab_no_negativo": bool(
            final_df["areas_verdes_m2_hab"].dropna().ge(0).all()
        ),
        "ipp_pesos_hab_no_negativo": bool(
            final_df["ipp_pesos_hab"].dropna().ge(0).all()
        ),
    }
    inf_counts = {
        "areas_verdes_m2_hab": int(final_df["areas_verdes_m2_hab"].isin([float("inf"), float("-inf")]).sum()),
        "ipp_pesos_hab": int(final_df["ipp_pesos_hab"].isin([float("inf"), float("-inf")]).sum()),
    }
    null_counts = {
        column: int(final_df[column].isna().sum())
        for column in (
            "poblacion",
            "pobreza_ingresos_pct",
            "areas_verdes_m2",
            "ipp_miles_pesos",
            "areas_verdes_m2_hab",
            "ipp_pesos_hab",
        )
    }
    return {
        "row_count": len(final_df),
        "column_count": len(final_df.columns),
        "codigo_unique": bool(final_df["codigo_comuna"].is_unique),
        "codigo_nulls": int(final_df["codigo_comuna"].isna().sum()),
        "null_counts": null_counts,
        "inf_counts": inf_counts,
        "numeric_checks": numeric_checks,
    }


def build_final_dataset(
    dim_base: pd.DataFrame | None = None,
    staging_tables: dict[str, pd.DataFrame] | None = None,
) -> tuple[pd.DataFrame, list[IntegrationStepEvidence], list[str], dict[str, object]]:
    dim_base = dim_base.copy() if dim_base is not None else _load_master_dimension()
    staging_tables = staging_tables or load_staging_sources()

    integrated = dim_base[["codigo_comuna", "nombre_comuna"]].copy()
    evidences: list[IntegrationStepEvidence] = []
    warnings: list[str] = []

    for source_id in INTEGRATION_SEQUENCE:
        integrated, evidence = _merge_source(integrated, source_id, staging_tables[source_id])
        evidences.append(evidence)
        if evidence.unmatched_rows:
            warnings.append(
                f"{evidence.source_label}: {evidence.unmatched_rows} comunas quedaron sin dato tras el merge."
            )

    final_df = create_derived_metrics(integrated)
    validation = _collect_final_validation(final_df)

    if validation["row_count"] != EXPECTED_DIM_COMUNA_ROWS:
        raise ValueError(
            "El dataset final no mantiene las 32 comunas requeridas tras la integracion."
        )
    if not validation["codigo_unique"] or validation["codigo_nulls"] != 0:
        raise ValueError("`codigo_comuna` no quedo como llave unica valida en el dataset final.")
    if any(count != 0 for count in validation["inf_counts"].values()):
        raise ValueError("Se detectaron valores infinitos en metricas derivadas.")
    if not all(validation["numeric_checks"].values()):
        raise ValueError("Las metricas derivadas contienen valores negativos no permitidos.")

    return final_df, evidences, warnings, validation


def export_final_dataset(
    final_df: pd.DataFrame,
    path: Path = FINAL_DATASET_PATH,
) -> None:
    ensure_directories()
    path.parent.mkdir(parents=True, exist_ok=True)
    final_df.to_csv(path, index=False, encoding="utf-8")


def export_integration_log(
    dim_base: pd.DataFrame,
    final_df: pd.DataFrame,
    evidences: list[IntegrationStepEvidence],
    warnings: list[str],
    validation: dict[str, object],
    path: Path = LOG_INTEGRACION_PATH,
) -> str:
    lines = [
        "# Log de integracion",
        "",
        "## Base maestra",
        f"- Archivo base: `{_relpath(DIM_COMUNA_BASE_PATH)}`",
        f"- Filas iniciales: {len(dim_base)}",
        "- Columnas base conservadas para integracion: `codigo_comuna`, `nombre_comuna`.",
        "- Llave de merge aplicada en toda la fase: `codigo_comuna`.",
        "",
        "## Evidencia de merges",
    ]

    for index, evidence in enumerate(evidences, start=1):
        lines.extend(
            [
                f"### Merge {index} - {evidence.source_label}",
                f"- Archivo staging: `{evidence.staging_path}`",
                "- Tipo de merge: `left` con validacion `one_to_one`.",
                f"- Filas antes: {evidence.rows_before}",
                f"- Filas despues: {evidence.rows_after}",
                f"- Columnas incorporadas: {', '.join(evidence.added_columns)}",
                "- Nulos relevantes despues del merge: "
                + ", ".join(
                    f"{column}={count}" for column, count in evidence.null_counts.items()
                ),
                f"- Duplicados en staging por `codigo_comuna`: {evidence.source_duplicates}",
                f"- Duplicados en resultado por `codigo_comuna`: {evidence.result_duplicates}",
                f"- Comunas sin dato de esta fuente tras el merge: {evidence.unmatched_rows}",
                "",
            ]
        )

    null_counts_text = ", ".join(
        f"{column}={count}" for column, count in validation["null_counts"].items()
    )
    inf_counts_text = ", ".join(
        f"{column}={count}" for column, count in validation["inf_counts"].items()
    )
    lines.extend(
        [
            "## Validacion final de integracion",
            f"- Filas finales: {validation['row_count']}",
            f"- Columnas finales: {validation['column_count']}",
            f"- `codigo_comuna` unico: {'si' if validation['codigo_unique'] else 'no'}.",
            f"- Nulos relevantes en dataset final: {null_counts_text}.",
            f"- Infinitos detectados en metricas derivadas: {inf_counts_text}.",
            "- `areas_verdes_m2_hab >= 0` cuando hay dato: "
            f"{'si' if validation['numeric_checks']['areas_verdes_m2_hab_no_negativo'] else 'no'}.",
            "- `ipp_pesos_hab >= 0` cuando hay dato: "
            f"{'si' if validation['numeric_checks']['ipp_pesos_hab_no_negativo'] else 'no'}.",
            "- Confirmacion: se mantuvieron 32 comunas y no se genero SQLite en esta fase.",
            "",
            "## Alertas",
        ]
    )

    if warnings:
        for warning in warnings:
            lines.append(f"- {warning}")
    else:
        lines.append("- No se detectaron alertas de merge ni perdida de comunas.")

    content = "\n".join(lines) + "\n"
    path.write_text(content, encoding="utf-8")
    return content


def export_dataset_summary(
    final_df: pd.DataFrame,
    warnings: list[str],
    path: Path = RESUMEN_DATASET_FINAL_PATH,
) -> str:
    lines = [
        "# Resumen del dataset final",
        "",
        "## Dataset generado",
        f"- Archivo: `{_relpath(FINAL_DATASET_PATH)}`",
        f"- Filas: {len(final_df)}",
        f"- Columnas: {len(final_df.columns)}",
        "- Unidad de analisis: una fila = una comuna.",
        "- Cobertura: Provincia de Santiago.",
        "",
        "## Columnas finales",
    ]

    for column in final_df.columns:
        lines.append(f"- `{column}`: {VARIABLE_DEFINITIONS[column]}")

    lines.extend(
        [
            "",
            "## Anios de referencia usados",
            f"- `anio_poblacion = {REFERENCE_YEARS['anio_poblacion']}`.",
            f"- `anio_pobreza = {REFERENCE_YEARS['anio_pobreza']}`.",
            f"- `anio_areas_verdes = {REFERENCE_YEARS['anio_areas_verdes']}`.",
            f"- `anio_ingresos = {REFERENCE_YEARS['anio_ingresos']}`.",
            "",
            "## Observaciones metodologicas",
            "- `nombre_comuna` proviene exclusivamente de `dim_comuna_base.csv`.",
            "- Los cuatro merges se hicieron como `left` sobre `codigo_comuna` y con control de cardinalidad `one_to_one`.",
            "- No se realizaron imputaciones. Los `NaN` corresponden a faltantes reales en staging o a divisiones invalidas por `poblacion` nula/no positiva.",
            "- El dataset queda preparado para validacion de calidad del resultado final en Fase 7.",
            "- Este dataset soporta analisis comparativo y descriptivo; no permite afirmar causalidad.",
            "",
            "## Alertas observadas",
        ]
    )

    if warnings:
        for warning in warnings:
            lines.append(f"- {warning}")
    else:
        lines.append("- No se detectaron alertas operativas durante la integracion.")

    content = "\n".join(lines) + "\n"
    path.write_text(content, encoding="utf-8")
    return content


def run_phase_6_integration() -> dict[str, object]:
    ensure_directories()
    dim_base = _load_master_dimension()
    staging_tables = load_staging_sources()
    final_df, evidences, warnings, validation = build_final_dataset(
        dim_base=dim_base,
        staging_tables=staging_tables,
    )

    export_final_dataset(final_df)
    log_markdown = export_integration_log(
        dim_base=dim_base,
        final_df=final_df,
        evidences=evidences,
        warnings=warnings,
        validation=validation,
    )
    summary_markdown = export_dataset_summary(
        final_df=final_df,
        warnings=warnings,
    )

    return {
        "master_dimension": dim_base,
        "staging_tables": staging_tables,
        "final_dataset": final_df,
        "merge_evidences": evidences,
        "warnings": warnings,
        "validation": validation,
        "final_dataset_path": FINAL_DATASET_PATH,
        "integration_log_path": LOG_INTEGRACION_PATH,
        "dataset_summary_path": RESUMEN_DATASET_FINAL_PATH,
        "integration_log_markdown": log_markdown,
        "dataset_summary_markdown": summary_markdown,
    }
