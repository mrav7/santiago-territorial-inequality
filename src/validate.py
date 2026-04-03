from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from config import (
    BASE_DIR,
    EXPECTED_DIM_COMUNA_ROWS,
    RESUMEN_TRANSFORMACIONES_PATH,
    STAGING_SOURCE_PATHS,
    VALIDACION_STAGING_PATH,
    ensure_directories,
)
from transform import StagingArtifact, TransformationEvidence

EXPECTED_STAGING_COLUMNS = {
    "A": (
        "codigo_comuna",
        "nombre_comuna",
        "mmpqc_2024",
        "mmpzc_2024",
        "areas_verdes_m2",
    ),
    "B": (
        "codigo_comuna",
        "nombre_comuna",
        "ipp_miles_pesos",
    ),
    "C": (
        "codigo_comuna",
        "nombre_comuna",
        "pobreza_ingresos_pct",
    ),
    "D": (
        "codigo_comuna",
        "nombre_comuna",
        "poblacion",
    ),
}


@dataclass(frozen=True)
class StagingValidationResult:
    source_id: str
    nombre_fuente: str
    is_valid: bool
    statuses: tuple[str, ...]
    warnings: tuple[str, ...]
    summary_row: dict[str, object]


def _relpath(path: Path) -> str:
    return path.relative_to(BASE_DIR).as_posix()


def _count_key_nulls(dataframe: pd.DataFrame) -> int:
    return int(dataframe[["codigo_comuna", "nombre_comuna"]].isna().sum().sum())


def _code_format_ok(series: pd.Series) -> bool:
    return bool(series.dropna().astype(str).str.fullmatch(r"\d{5}").all())


def _range_validation_text(source_id: str, dataframe: pd.DataFrame) -> tuple[bool, str]:
    if source_id == "A":
        ok = bool(dataframe["areas_verdes_m2"].dropna().ge(0).all())
        return ok, "areas_verdes_m2 >= 0"
    if source_id == "B":
        ok = bool(dataframe["ipp_miles_pesos"].dropna().ge(0).all())
        return ok, "ipp_miles_pesos >= 0"
    if source_id == "C":
        ok = bool(dataframe["pobreza_ingresos_pct"].dropna().between(0, 100).all())
        return ok, "pobreza_ingresos_pct entre 0 y 100"
    ok = bool(dataframe["poblacion"].dropna().gt(0).all())
    return ok, "poblacion > 0"


def validate_staging_outputs(
    staging_tables: dict[str, pd.DataFrame],
    dim_base: pd.DataFrame,
    artifacts: dict[str, StagingArtifact],
    evidences: dict[str, TransformationEvidence],
) -> dict[str, StagingValidationResult]:
    results: dict[str, StagingValidationResult] = {}
    expected_codes = list(dim_base["codigo_comuna"].astype(int).map(lambda value: f"{value:05d}"))

    for source_id, dataframe in staging_tables.items():
        artifact = artifacts[source_id]
        evidence = evidences[source_id]

        statuses: list[str] = []
        warnings: list[str] = []

        actual_columns = tuple(map(str, dataframe.columns))
        expected_columns = EXPECTED_STAGING_COLUMNS[source_id]
        if actual_columns == expected_columns:
            statuses.append("[OK] Las columnas finales coinciden con el esquema esperado.")
        else:
            statuses.append(
                f"[ERROR] El esquema final no coincide con lo esperado: {expected_columns}."
            )

        if len(dataframe) == EXPECTED_DIM_COMUNA_ROWS:
            statuses.append(
                f"[OK] La tabla contiene {EXPECTED_DIM_COMUNA_ROWS} comunas del universo final."
            )
        else:
            statuses.append(
                f"[ERROR] La tabla contiene {len(dataframe)} filas; se esperaban {EXPECTED_DIM_COMUNA_ROWS}."
            )

        duplicates = int(dataframe["codigo_comuna"].duplicated().sum())
        if duplicates == 0:
            statuses.append("[OK] `codigo_comuna` es unico en la salida staging.")
        else:
            statuses.append(
                f"[ERROR] `codigo_comuna` tiene {duplicates} duplicados en staging."
            )

        key_nulls = _count_key_nulls(dataframe)
        if key_nulls == 0:
            statuses.append("[OK] No hay nulos en las columnas clave.")
        else:
            statuses.append(f"[ERROR] Hay {key_nulls} nulos en columnas clave.")

        if _code_format_ok(dataframe["codigo_comuna"]):
            statuses.append("[OK] `codigo_comuna` quedo como string consistente de 5 digitos.")
        else:
            statuses.append("[ERROR] `codigo_comuna` no cumple el formato esperado de 5 digitos.")

        observed_codes = list(dataframe["codigo_comuna"].dropna().astype(str))
        missing_codes = sorted(set(expected_codes) - set(observed_codes))
        extra_codes = sorted(set(observed_codes) - set(expected_codes))
        if not missing_codes and not extra_codes:
            statuses.append("[OK] La cobertura comunal coincide exactamente con la dimension maestra.")
        else:
            statuses.append(
                "[ERROR] La cobertura comunal no coincide con la dimension maestra "
                f"(faltantes={missing_codes}, extras={extra_codes})."
            )

        merged_names = dataframe.merge(
            dim_base.assign(
                codigo_comuna=dim_base["codigo_comuna"].astype(int).map(lambda value: f"{value:05d}")
            )[["codigo_comuna", "nombre_comuna"]],
            on="codigo_comuna",
            how="left",
            suffixes=("_staging", "_base"),
        )
        mismatched_names = merged_names[
            merged_names["nombre_comuna_staging"] != merged_names["nombre_comuna_base"]
        ]
        if mismatched_names.empty:
            statuses.append("[OK] `nombre_comuna` quedo estandarizado contra la base maestra.")
        else:
            statuses.append(
                f"[ERROR] Hay {len(mismatched_names)} nombres de comuna no estandarizados."
            )

        range_ok, range_rule = _range_validation_text(source_id, dataframe)
        if range_ok:
            statuses.append(f"[OK] Se cumple la validacion de rango: {range_rule}.")
        else:
            statuses.append(f"[ERROR] Falla la validacion de rango: {range_rule}.")

        if artifact.path.exists():
            statuses.append(f"[OK] Archivo staging exportado: {_relpath(artifact.path)}.")
        else:
            statuses.append(f"[ERROR] No existe el archivo staging {_relpath(artifact.path)}.")

        data_columns = [column for column in dataframe.columns if column not in {"codigo_comuna", "nombre_comuna"}]
        all_null_rows = int(dataframe[data_columns].isna().all(axis=1).sum())
        if all_null_rows:
            warnings.append(
                f"Hay {all_null_rows} filas del universo final sin datos en las variables de la fuente."
            )

        is_valid = not any(status.startswith("[ERROR]") for status in statuses)
        summary_row = {
            "source_id": source_id,
            "nombre_fuente": evidence.nombre_fuente,
            "archivo_raw_origen": evidence.raw_path,
            "archivo_logico": evidence.archivo_logico,
            "archivo_staging_generado": evidence.staging_path,
            "filas_antes": evidence.filas_antes,
            "filas_despues": evidence.filas_despues,
            "columnas_finales": " | ".join(dataframe.columns),
            "duplicados_codigo_comuna": duplicates,
            "nulos_clave": key_nulls,
            "fuera_de_universo_detectados": evidence.fuera_de_universo_detectados,
            "validacion_rango": f"{'OK' if range_ok else 'ERROR'}: {range_rule}",
            "estado": "OK" if is_valid else "ERROR",
        }

        results[source_id] = StagingValidationResult(
            source_id=source_id,
            nombre_fuente=evidence.nombre_fuente,
            is_valid=is_valid,
            statuses=tuple(statuses),
            warnings=tuple(warnings),
            summary_row=summary_row,
        )

    return results


def export_validacion_staging(
    validation_results: dict[str, StagingValidationResult],
    path: Path = VALIDACION_STAGING_PATH,
) -> pd.DataFrame:
    ensure_directories()
    rows = [
        validation_results[source_id].summary_row
        for source_id in sorted(validation_results)
    ]
    dataframe = pd.DataFrame(rows)
    dataframe.to_csv(path, index=False, encoding="utf-8")
    return dataframe


def build_transformations_summary(
    evidences: dict[str, TransformationEvidence],
    validation_results: dict[str, StagingValidationResult],
) -> str:
    lines = [
        "# Resumen de transformaciones a staging",
        "",
        "Este documento resume la trazabilidad y las reglas aplicadas en Fase 4 y Fase 5.",
        "",
    ]

    for source_id in sorted(evidences):
        evidence = evidences[source_id]
        validation = validation_results[source_id]
        lines.extend(
            [
                f"## Fuente {source_id} - {evidence.nombre_fuente}",
                f"- Archivo raw origen: `{evidence.raw_path}`",
                f"- Fuente logica / archivo logico: `{evidence.archivo_logico}`",
                f"- Archivo staging generado: `{evidence.staging_path}`",
                f"- Filas antes: {evidence.filas_antes}",
                f"- Filas despues: {evidence.filas_despues}",
                f"- Fuera de universo detectados: {evidence.fuera_de_universo_detectados}",
                f"- Filas sin codigo comunal valido excluidas: {evidence.filas_sin_codigo_excluidas}",
                f"- Duplicados por `codigo_comuna` en staging: {evidence.duplicados_codigo_comuna}",
                f"- Columnas originales consideradas: {', '.join(evidence.columnas_originales_consideradas)}",
                f"- Columnas finales conservadas: {', '.join(evidence.columnas_finales)}",
                f"- Renombres realizados: {'; '.join(evidence.renombres_realizados)}",
                f"- Tipos convertidos: {'; '.join(evidence.tipos_convertidos)}",
                f"- Valores especiales tratados: {'; '.join(evidence.valores_especiales_tratados)}",
                f"- Filtros aplicados: {'; '.join(evidence.filtros_aplicados)}",
                "- Validaciones ejecutadas:",
            ]
        )
        for status in validation.statuses:
            lines.append(f"  {status}")
        lines.append("- Observaciones o limitaciones pendientes:")
        for observation in evidence.observaciones:
            lines.append(f"  {observation}")
        for warning in validation.warnings:
            lines.append(f"  {warning}")
        lines.append("")

    lines.extend(
        [
            "## Estado",
            "- Las tablas staging quedan listas para merge posterior, pero aun no existe dataset final integrado.",
            "- No se genera SQLite en esta fase.",
        ]
    )
    return "\n".join(lines) + "\n"


def export_transformations_summary(
    summary_markdown: str,
    path: Path = RESUMEN_TRANSFORMACIONES_PATH,
) -> None:
    ensure_directories()
    path.write_text(summary_markdown, encoding="utf-8")


def run_phase_5_validation(
    staging_tables: dict[str, pd.DataFrame],
    dim_base: pd.DataFrame,
    artifacts: dict[str, StagingArtifact],
    evidences: dict[str, TransformationEvidence],
) -> dict[str, object]:
    validation_results = validate_staging_outputs(
        staging_tables=staging_tables,
        dim_base=dim_base,
        artifacts=artifacts,
        evidences=evidences,
    )
    validation_df = export_validacion_staging(validation_results)
    summary_markdown = build_transformations_summary(
        evidences=evidences,
        validation_results=validation_results,
    )
    export_transformations_summary(summary_markdown)
    return {
        "validation_results": validation_results,
        "validation_df": validation_df,
        "summary_markdown": summary_markdown,
        "summary_path": RESUMEN_TRANSFORMACIONES_PATH,
        "validation_path": VALIDACION_STAGING_PATH,
        "staging_paths": STAGING_SOURCE_PATHS,
    }
