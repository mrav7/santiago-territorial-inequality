from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from config import (
    BASE_DIR,
    EXPECTED_DIM_COMUNA_ROWS,
    PROCESSED_SOURCE_PATHS,
    RESUMEN_FASE_45_PATH,
    RESUMEN_HOMOLOGACION_PATH,
    STAGING_SOURCE_PATHS,
    ensure_directories,
)
from transform import TableArtifact

EXPECTED_PROCESSED_COLUMNS = {
    "A": (
        "codigo_comuna",
        "nombre_comuna",
        "areas_verdes_parques_m2_2024",
        "areas_verdes_plazas_m2_2024",
        "areas_verdes_total_m2_2024",
    ),
    "B": (
        "codigo_comuna",
        "nombre_comuna",
        "ipp_miles_pesos_2024",
    ),
    "C": (
        "codigo_comuna",
        "nombre_comuna",
        "personas_proyectadas_2022",
        "personas_pobreza_ingresos_2022",
        "pobreza_ingresos_pct_2022",
        "pobreza_ingresos_pct_limite_inferior_2022",
        "pobreza_ingresos_pct_limite_superior_2022",
    ),
    "D": (
        "codigo_comuna",
        "nombre_comuna",
        "poblacion_censada_2024",
        "hombres_2024",
        "mujeres_2024",
        "razon_hombre_mujer_2024",
    ),
}


@dataclass(frozen=True)
class SourceValidationResult:
    source_id: str
    path: Path
    is_valid: bool
    row_count: int
    null_counts: dict[str, int]
    statuses: tuple[str, ...]
    warnings: tuple[str, ...]


def _relpath(path: Path) -> str:
    return path.relative_to(BASE_DIR).as_posix()


def _series_equal_with_na(left: pd.Series, right: pd.Series) -> bool:
    left_safe = left.astype("object").where(left.notna(), "__NA__")
    right_safe = right.astype("object").where(right.notna(), "__NA__")
    return left_safe.astype(str).equals(right_safe.astype(str))


def _non_negative(series: pd.Series) -> bool:
    return bool(series.dropna().ge(0).all())


def _common_validation(
    source_id: str,
    dataframe: pd.DataFrame,
    dim_base: pd.DataFrame,
    path: Path,
) -> tuple[list[str], list[str], dict[str, int]]:
    statuses: list[str] = []
    warnings: list[str] = []
    null_counts = {
        column: int(dataframe[column].isna().sum())
        for column in dataframe.columns
        if column not in {"codigo_comuna", "nombre_comuna"}
    }

    expected_columns = EXPECTED_PROCESSED_COLUMNS[source_id]
    actual_columns = tuple(map(str, dataframe.columns))
    if actual_columns == expected_columns:
        statuses.append("[OK] La tabla tiene el esquema esperado.")
    else:
        statuses.append(
            f"[ERROR] El esquema no coincide con el esperado: {expected_columns}."
        )

    if len(dataframe) == EXPECTED_DIM_COMUNA_ROWS:
        statuses.append(
            f"[OK] La tabla contiene {EXPECTED_DIM_COMUNA_ROWS} filas, una por comuna objetivo."
        )
    else:
        statuses.append(
            f"[ERROR] La tabla contiene {len(dataframe)} filas; se esperaban {EXPECTED_DIM_COMUNA_ROWS}."
        )

    duplicate_codes = int(dataframe["codigo_comuna"].duplicated().sum())
    if duplicate_codes == 0:
        statuses.append("[OK] `codigo_comuna` es unico en la tabla limpia.")
    else:
        statuses.append(
            f"[ERROR] `codigo_comuna` presenta {duplicate_codes} duplicados en la tabla limpia."
        )

    observed_codes = set(dataframe["codigo_comuna"].dropna().astype(int))
    expected_codes = set(dim_base["codigo_comuna"].dropna().astype(int))
    missing_codes = sorted(expected_codes - observed_codes)
    extra_codes = sorted(observed_codes - expected_codes)
    if not missing_codes and not extra_codes:
        statuses.append("[OK] La cobertura comunal coincide exactamente con la dimension maestra.")
    else:
        statuses.append(
            "[ERROR] La cobertura comunal no coincide con la dimension maestra "
            f"(faltantes={missing_codes}, extras={extra_codes})."
        )

    merged_names = dim_base[["codigo_comuna", "nombre_comuna"]].merge(
        dataframe[["codigo_comuna", "nombre_comuna"]],
        on="codigo_comuna",
        how="left",
        suffixes=("_base", "_tabla"),
    )
    mismatched_names = merged_names[
        merged_names["nombre_comuna_base"] != merged_names["nombre_comuna_tabla"]
    ]
    if mismatched_names.empty:
        statuses.append("[OK] `nombre_comuna` quedo estandarizado contra la dimension maestra.")
    else:
        statuses.append(
            f"[ERROR] Hay {len(mismatched_names)} diferencias de nombre frente a la base maestra."
        )

    null_columns = {column: count for column, count in null_counts.items() if count > 0}
    if null_columns:
        warning_text = ", ".join(f"{column}={count}" for column, count in null_columns.items())
        warnings.append(f"Nulos presentes en columnas de datos: {warning_text}.")

    data_columns = [column for column in dataframe.columns if column not in {"codigo_comuna", "nombre_comuna"}]
    fully_null_rows = int(dataframe[data_columns].isna().all(axis=1).sum())
    if fully_null_rows:
        statuses.append(
            f"[ERROR] Hay {fully_null_rows} comunas sin datos en ninguna variable de la tabla limpia."
        )

    if not path.exists():
        statuses.append(f"[ERROR] No existe el archivo exportado {_relpath(path)}.")
    else:
        statuses.append(f"[OK] Archivo exportado: {_relpath(path)}.")

    return statuses, warnings, null_counts


def _validate_source_a(dataframe: pd.DataFrame) -> tuple[list[str], list[str]]:
    statuses: list[str] = []
    warnings: list[str] = []

    numeric_columns = [
        "areas_verdes_parques_m2_2024",
        "areas_verdes_plazas_m2_2024",
        "areas_verdes_total_m2_2024",
    ]
    for column in numeric_columns:
        if _non_negative(dataframe[column]):
            statuses.append(f"[OK] `{column}` no contiene valores negativos.")
        else:
            statuses.append(f"[ERROR] `{column}` contiene valores negativos.")

    expected_total = dataframe[
        [
            "areas_verdes_parques_m2_2024",
            "areas_verdes_plazas_m2_2024",
        ]
    ].sum(axis=1, min_count=2).astype("Int64")
    if _series_equal_with_na(expected_total, dataframe["areas_verdes_total_m2_2024"]):
        statuses.append("[OK] El total de areas verdes coincide con la suma de parques y plazas.")
    else:
        statuses.append("[ERROR] El total de areas verdes no coincide con sus componentes.")

    return statuses, warnings


def _validate_source_b(dataframe: pd.DataFrame) -> tuple[list[str], list[str]]:
    if _non_negative(dataframe["ipp_miles_pesos_2024"]):
        return ["[OK] `ipp_miles_pesos_2024` no contiene valores negativos."], []
    return ["[ERROR] `ipp_miles_pesos_2024` contiene valores negativos."], []


def _validate_source_c(dataframe: pd.DataFrame) -> tuple[list[str], list[str]]:
    statuses: list[str] = []
    warnings: list[str] = []

    count_columns = [
        "personas_proyectadas_2022",
        "personas_pobreza_ingresos_2022",
    ]
    pct_columns = [
        "pobreza_ingresos_pct_2022",
        "pobreza_ingresos_pct_limite_inferior_2022",
        "pobreza_ingresos_pct_limite_superior_2022",
    ]

    if all(_non_negative(dataframe[column]) for column in count_columns):
        statuses.append("[OK] Los conteos de poblacion y pobreza son no negativos.")
    else:
        statuses.append("[ERROR] Hay conteos negativos en la fuente de pobreza.")

    pct_in_range = all(
        bool(dataframe[column].dropna().between(0, 100).all())
        for column in pct_columns
    )
    if pct_in_range:
        statuses.append("[OK] Las tasas de pobreza quedaron expresadas como porcentaje 0-100.")
    else:
        statuses.append("[ERROR] Hay porcentajes de pobreza fuera del rango 0-100.")

    interval_ok = bool(
        (
            dataframe["pobreza_ingresos_pct_limite_inferior_2022"]
            <= dataframe["pobreza_ingresos_pct_2022"]
        ).all()
        and (
            dataframe["pobreza_ingresos_pct_2022"]
            <= dataframe["pobreza_ingresos_pct_limite_superior_2022"]
        ).all()
    )
    if interval_ok:
        statuses.append("[OK] El porcentaje puntual queda dentro del intervalo inferior/superior.")
    else:
        statuses.append("[ERROR] Hay intervalos de pobreza inconsistentes.")

    return statuses, warnings


def _validate_source_d(dataframe: pd.DataFrame) -> tuple[list[str], list[str]]:
    statuses: list[str] = []
    warnings: list[str] = []

    count_columns = [
        "poblacion_censada_2024",
        "hombres_2024",
        "mujeres_2024",
    ]
    if all(_non_negative(dataframe[column]) for column in count_columns):
        statuses.append("[OK] Los conteos poblacionales son no negativos.")
    else:
        statuses.append("[ERROR] Hay conteos poblacionales negativos.")

    composition_ok = _series_equal_with_na(
        dataframe["hombres_2024"] + dataframe["mujeres_2024"],
        dataframe["poblacion_censada_2024"],
    )
    if composition_ok:
        statuses.append("[OK] `hombres_2024 + mujeres_2024` coincide con la poblacion censada.")
    else:
        statuses.append("[ERROR] La composicion por sexo no cuadra con la poblacion censada.")

    if bool(dataframe["razon_hombre_mujer_2024"].dropna().gt(0).all()):
        statuses.append("[OK] `razon_hombre_mujer_2024` contiene valores positivos.")
    else:
        statuses.append("[ERROR] `razon_hombre_mujer_2024` contiene valores no validos.")

    return statuses, warnings


SOURCE_VALIDATORS = {
    "A": _validate_source_a,
    "B": _validate_source_b,
    "C": _validate_source_c,
    "D": _validate_source_d,
}


def validate_processed_tables(
    processed_tables: dict[str, pd.DataFrame],
    dim_base: pd.DataFrame,
    processed_artifacts: dict[str, TableArtifact],
) -> dict[str, SourceValidationResult]:
    results: dict[str, SourceValidationResult] = {}
    for source_id, dataframe in processed_tables.items():
        common_statuses, common_warnings, null_counts = _common_validation(
            source_id=source_id,
            dataframe=dataframe,
            dim_base=dim_base,
            path=processed_artifacts[source_id].path,
        )
        source_statuses, source_warnings = SOURCE_VALIDATORS[source_id](dataframe)
        statuses = tuple(common_statuses + source_statuses)
        warnings = tuple(common_warnings + source_warnings)
        is_valid = not any(status.startswith("[ERROR]") for status in statuses)
        results[source_id] = SourceValidationResult(
            source_id=source_id,
            path=processed_artifacts[source_id].path,
            is_valid=is_valid,
            row_count=len(dataframe),
            null_counts=null_counts,
            statuses=statuses,
            warnings=warnings,
        )
    return results


def build_phase_45_summary_markdown(
    staging_artifacts: dict[str, TableArtifact],
    processed_artifacts: dict[str, TableArtifact],
    validation_results: dict[str, SourceValidationResult],
) -> str:
    lines = [
        "# Resumen Fase 4 y Fase 5",
        "",
        "## Fase 4 - Staging reproducible",
        "- La extraccion queda materializada como tablas crudas parseadas, una por fuente, sin integrar aun el dataset final.",
        "- Los archivos de staging preservan la estructura leida desde cada fuente y sirven como base reproducible para las transformaciones posteriores.",
        "",
    ]

    for source_id in sorted(staging_artifacts):
        artifact = staging_artifacts[source_id]
        lines.append(
            f"- Fuente {source_id}: `{_relpath(artifact.path)}` con {artifact.row_count} filas y {artifact.column_count} columnas."
        )

    lines.extend(
        [
            "",
            "## Fase 5 - Reglas de transformacion",
            "- Fuente A: `No Aplica` se interpreta como 0 solo para componentes de areas verdes; `No Recepcionado` permanece como nulo. El total se calcula como parques + plazas.",
            "- Fuente B: el IPP se conserva en miles de pesos nominales 2024.",
            "- Fuente C: las tasas de pobreza pasan de proporcion 0-1 a porcentaje 0-100.",
            "- Fuente D: la tabla comunal queda filtrada al universo final de 32 comunas y se excluyen filas agregadas o notas al trabajar por `codigo_comuna`.",
            "",
            "## Tablas limpias listas para merge",
        ]
    )

    for source_id in sorted(processed_artifacts):
        artifact = processed_artifacts[source_id]
        validation = validation_results[source_id]
        status_label = "OK" if validation.is_valid else "ERROR"
        lines.append(
            f"- Fuente {source_id}: `{_relpath(artifact.path)}` con {artifact.row_count} filas y {artifact.column_count} columnas. Estado={status_label}."
        )
        null_columns = {
            column: count
            for column, count in validation.null_counts.items()
            if count > 0
        }
        if null_columns:
            null_text = ", ".join(f"{column}={count}" for column, count in null_columns.items())
            lines.append(f"  Nulos en datos: {null_text}.")

    lines.extend(
        [
            "",
            "## Validacion de salida",
        ]
    )

    for source_id in sorted(validation_results):
        validation = validation_results[source_id]
        lines.append(f"- Fuente {source_id}:")
        for status in validation.statuses:
            lines.append(f"  {status}")
        for warning in validation.warnings:
            lines.append(f"  [OBSERVACION] {warning}")

    lines.extend(
        [
            "",
            "## Estado del proyecto",
            f"- Sigue vigente la homologacion comunal de `{_relpath(RESUMEN_HOMOLOGACION_PATH)}` como soporte de trazabilidad.",
            "- No se integra aun el dataset final comunal.",
            "- No se carga aun ningun archivo SQLite.",
        ]
    )

    return "\n".join(lines) + "\n"


def export_phase_45_summary(summary_markdown: str, path: Path = RESUMEN_FASE_45_PATH) -> None:
    ensure_directories()
    path.write_text(summary_markdown, encoding="utf-8")


def run_phase_45_validate_outputs(
    staging_artifacts: dict[str, TableArtifact],
    processed_tables: dict[str, pd.DataFrame],
    processed_artifacts: dict[str, TableArtifact],
    dim_base: pd.DataFrame,
) -> dict[str, object]:
    validation_results = validate_processed_tables(
        processed_tables=processed_tables,
        dim_base=dim_base,
        processed_artifacts=processed_artifacts,
    )
    summary_markdown = build_phase_45_summary_markdown(
        staging_artifacts=staging_artifacts,
        processed_artifacts=processed_artifacts,
        validation_results=validation_results,
    )
    export_phase_45_summary(summary_markdown)
    overall_valid = all(result.is_valid for result in validation_results.values())
    return {
        "is_valid": overall_valid,
        "validation_results": validation_results,
        "summary_markdown": summary_markdown,
        "summary_path": RESUMEN_FASE_45_PATH,
        "staging_paths": STAGING_SOURCE_PATHS,
        "processed_paths": PROCESSED_SOURCE_PATHS,
    }
