from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from config import (
    BASE_DIR,
    FINAL_DATASET_PATH,
    EXPECTED_DIM_COMUNA_ROWS,
    REPORTE_VALIDACION_FINAL_CSV_PATH,
    REPORTE_VALIDACION_FINAL_MD_PATH,
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

EXPECTED_FINAL_DATASET_COLUMNS = (
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

FINAL_NUMERIC_COLUMNS = (
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

EXPECTED_REFERENCE_YEARS = {
    "anio_poblacion": 2024,
    "anio_pobreza": 2022,
    "anio_areas_verdes": 2024,
    "anio_ingresos": 2024,
}


@dataclass(frozen=True)
class StagingValidationResult:
    source_id: str
    nombre_fuente: str
    is_valid: bool
    statuses: tuple[str, ...]
    warnings: tuple[str, ...]
    summary_row: dict[str, object]


@dataclass(frozen=True)
class FinalValidationCheck:
    check_id: str
    description: str
    is_valid: bool
    observed_value: str
    expected_value: str
    detail: str

    @property
    def status_label(self) -> str:
        return "OK" if self.is_valid else "ERROR"


@dataclass(frozen=True)
class FinalDatasetValidationResult:
    dataset_path: str
    row_count: int
    column_count: int
    is_valid: bool
    checks: tuple[FinalValidationCheck, ...]
    null_counts: dict[str, int]
    numeric_convertibility_errors: dict[str, int]
    missing_codes: tuple[str, ...]
    extra_codes: tuple[str, ...]
    summary_row: dict[str, object]


def _relpath(path: Path) -> str:
    return path.relative_to(BASE_DIR).as_posix()


def _count_key_nulls(dataframe: pd.DataFrame) -> int:
    return int(dataframe[["codigo_comuna", "nombre_comuna"]].isna().sum().sum())


def _code_format_ok(series: pd.Series) -> bool:
    return bool(series.dropna().astype(str).str.fullmatch(r"\d{5}").all())


def _clean_string_series(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().replace("", pd.NA)


def _normalize_codigo_comuna(series: pd.Series) -> pd.Series:
    cleaned = _clean_string_series(series)
    numeric = pd.to_numeric(cleaned, errors="coerce").astype("Int64")
    return numeric.map(
        lambda value: f"{int(value):05d}" if pd.notna(value) else pd.NA
    ).astype("string")


def _to_numeric_series(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def _append_final_check(
    checks: list[FinalValidationCheck],
    check_id: str,
    description: str,
    is_valid: bool,
    observed_value: object,
    expected_value: object,
    detail: str,
) -> None:
    checks.append(
        FinalValidationCheck(
            check_id=check_id,
            description=description,
            is_valid=bool(is_valid),
            observed_value=str(observed_value),
            expected_value=str(expected_value),
            detail=detail,
        )
    )


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


def load_final_dataset(path: Path = FINAL_DATASET_PATH) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"No existe el dataset final: {_relpath(path)}")
    dataframe = pd.read_csv(path, dtype={"codigo_comuna": "string"})
    dataframe["codigo_comuna"] = _clean_string_series(dataframe["codigo_comuna"])
    return dataframe


def validate_final_dataset(
    final_df: pd.DataFrame,
    dim_base: pd.DataFrame,
    dataset_path: Path = FINAL_DATASET_PATH,
) -> FinalDatasetValidationResult:
    dataframe = final_df.copy()
    checks: list[FinalValidationCheck] = []

    dataframe["codigo_comuna"] = _clean_string_series(dataframe["codigo_comuna"])
    normalized_codes = _normalize_codigo_comuna(dataframe["codigo_comuna"])
    dim_codes = _normalize_codigo_comuna(dim_base["codigo_comuna"])
    dim_lookup = dim_base.assign(codigo_comuna=dim_codes)[["codigo_comuna", "nombre_comuna"]]

    actual_columns = tuple(map(str, dataframe.columns))
    missing_columns = sorted(set(EXPECTED_FINAL_DATASET_COLUMNS) - set(actual_columns))
    extra_columns = sorted(set(actual_columns) - set(EXPECTED_FINAL_DATASET_COLUMNS))
    _append_final_check(
        checks,
        "columnas_esperadas",
        "El dataset final contiene exactamente las columnas esperadas.",
        not missing_columns and not extra_columns,
        " | ".join(actual_columns),
        " | ".join(EXPECTED_FINAL_DATASET_COLUMNS),
        (
            "Sin diferencias de esquema."
            if not missing_columns and not extra_columns
            else f"faltantes={missing_columns}; extras={extra_columns}"
        ),
    )

    _append_final_check(
        checks,
        "fila_por_comuna",
        "Existe una sola fila por comuna.",
        len(dataframe) == int(normalized_codes.nunique(dropna=True)),
        f"filas={len(dataframe)}; comunas_unicas={int(normalized_codes.nunique(dropna=True))}",
        "filas == comunas_unicas",
        "Sin multiplicacion de filas por comuna."
        if len(dataframe) == int(normalized_codes.nunique(dropna=True))
        else "El numero de filas no coincide con las comunas unicas observadas.",
    )

    codigo_nulls = int(dataframe["codigo_comuna"].isna().sum())
    _append_final_check(
        checks,
        "codigo_comuna_no_nulo",
        "`codigo_comuna` no contiene nulos.",
        codigo_nulls == 0,
        codigo_nulls,
        0,
        "Llave primaria completa." if codigo_nulls == 0 else "Hay codigos nulos o en blanco.",
    )

    code_format_ok = _code_format_ok(dataframe["codigo_comuna"])
    _append_final_check(
        checks,
        "codigo_comuna_formato",
        "`codigo_comuna` mantiene formato string de 5 digitos.",
        code_format_ok,
        "OK" if code_format_ok else "INVALIDO",
        "regex ^\\d{5}$",
        "Todos los codigos cumplen el formato esperado."
        if code_format_ok
        else "Se detectaron codigos con formato inesperado.",
    )

    code_duplicates = int(normalized_codes.duplicated().sum())
    _append_final_check(
        checks,
        "codigo_comuna_unico",
        "`codigo_comuna` es unico.",
        code_duplicates == 0,
        code_duplicates,
        0,
        "Sin duplicados por llave." if code_duplicates == 0 else "Existen duplicados por llave.",
    )

    _append_final_check(
        checks,
        "cantidad_comunas",
        "El dataset final contiene exactamente 32 comunas.",
        len(dataframe) == EXPECTED_DIM_COMUNA_ROWS,
        len(dataframe),
        EXPECTED_DIM_COMUNA_ROWS,
        "Cobertura total observada." if len(dataframe) == EXPECTED_DIM_COMUNA_ROWS else "Cantidad de filas distinta al universo esperado.",
    )

    observed_codes = set(normalized_codes.dropna().astype(str))
    expected_codes = set(dim_codes.dropna().astype(str))
    missing_codes = tuple(sorted(expected_codes - observed_codes))
    extra_codes = tuple(sorted(observed_codes - expected_codes))
    coverage_ok = not missing_codes and not extra_codes
    _append_final_check(
        checks,
        "cobertura_dim_base",
        "La cobertura comunal coincide con `dim_comuna_base.csv`.",
        coverage_ok,
        f"faltantes={list(missing_codes)}; extras={list(extra_codes)}",
        "sin faltantes ni extras",
        "Cobertura exacta contra la base maestra."
        if coverage_ok
        else "La cobertura final difiere de la dimension maestra.",
    )

    names_join = dataframe.assign(codigo_comuna=normalized_codes).merge(
        dim_lookup,
        on="codigo_comuna",
        how="left",
        suffixes=("_final", "_base"),
    )
    name_mismatches = names_join[
        names_join["nombre_comuna_final"].astype("string") != names_join["nombre_comuna_base"].astype("string")
    ]
    _append_final_check(
        checks,
        "nombre_comuna_base",
        "`nombre_comuna` coincide con la base maestra.",
        name_mismatches.empty,
        len(name_mismatches),
        0,
        "Los nombres finales preservan la base maestra."
        if name_mismatches.empty
        else "Hay comunas cuyo nombre final difiere de `dim_comuna_base.csv`.",
    )

    numeric_convertibility_errors: dict[str, int] = {}
    numeric_series: dict[str, pd.Series] = {}
    for column in FINAL_NUMERIC_COLUMNS:
        series = dataframe[column] if column in dataframe.columns else pd.Series(dtype="object")
        converted = _to_numeric_series(series)
        invalid_count = int(series.notna().sum() - converted.notna().sum())
        numeric_convertibility_errors[column] = invalid_count
        numeric_series[column] = converted

    convertibility_ok = all(count == 0 for count in numeric_convertibility_errors.values())
    _append_final_check(
        checks,
        "convertibilidad_numerica",
        "Las columnas numericas son convertibles a tipo numerico razonable.",
        convertibility_ok,
        "; ".join(f"{column}={count}" for column, count in numeric_convertibility_errors.items()),
        "0 errores de conversion",
        "Todas las columnas numericas son convertibles."
        if convertibility_ok
        else "Existen valores no convertibles en columnas numericas.",
    )

    years_ok = True
    years_detail: list[str] = []
    for column, expected_year in EXPECTED_REFERENCE_YEARS.items():
        observed = sorted(numeric_series[column].dropna().astype(int).unique().tolist())
        if observed != [expected_year]:
            years_ok = False
        years_detail.append(f"{column}={observed}")
    _append_final_check(
        checks,
        "anios_referencia",
        "Los anios de referencia permanecen consistentes con Fase 6.",
        years_ok,
        "; ".join(years_detail),
        "; ".join(f"{column}={[year]}" for column, year in EXPECTED_REFERENCE_YEARS.items()),
        "Anios de referencia consistentes."
        if years_ok
        else "Se detectaron anios distintos a los documentados.",
    )

    population = numeric_series["poblacion"]
    population_ok = bool(population.gt(0).all())
    _append_final_check(
        checks,
        "poblacion_positiva",
        "`poblacion` es estrictamente mayor que 0.",
        population_ok,
        int((~population.gt(0)).sum()),
        0,
        "Toda la poblacion es positiva."
        if population_ok
        else "Hay filas con poblacion nula, no convertible o no positiva.",
    )

    pobreza = numeric_series["pobreza_ingresos_pct"]
    pobreza_invalid = int((~pobreza.dropna().between(0, 100)).sum())
    _append_final_check(
        checks,
        "pobreza_rango",
        "`pobreza_ingresos_pct` queda entre 0 y 100 cuando hay dato.",
        pobreza_invalid == 0,
        pobreza_invalid,
        0,
        "La variable de pobreza esta dentro de rango."
        if pobreza_invalid == 0
        else "Hay valores fuera del rango 0-100.",
    )

    areas_verdes = numeric_series["areas_verdes_m2"]
    areas_invalid = int((~areas_verdes.dropna().ge(0)).sum())
    _append_final_check(
        checks,
        "areas_verdes_no_negativas",
        "`areas_verdes_m2` es no negativa cuando hay dato.",
        areas_invalid == 0,
        areas_invalid,
        0,
        "Sin areas verdes negativas."
        if areas_invalid == 0
        else "Hay valores negativos en `areas_verdes_m2`.",
    )

    ipp = numeric_series["ipp_miles_pesos"]
    ipp_invalid = int((~ipp.dropna().ge(0)).sum())
    _append_final_check(
        checks,
        "ipp_no_negativo",
        "`ipp_miles_pesos` es no negativo cuando hay dato.",
        ipp_invalid == 0,
        ipp_invalid,
        0,
        "Sin IPP negativos."
        if ipp_invalid == 0
        else "Hay valores negativos en `ipp_miles_pesos`.",
    )

    areas_hab = numeric_series["areas_verdes_m2_hab"]
    areas_inf = int(areas_hab.isin([float("inf"), float("-inf")]).sum())
    _append_final_check(
        checks,
        "areas_verdes_m2_hab_sin_inf",
        "`areas_verdes_m2_hab` no contiene infinitos.",
        areas_inf == 0,
        areas_inf,
        0,
        "Sin infinitos en areas verdes por habitante."
        if areas_inf == 0
        else "Se detectaron infinitos en `areas_verdes_m2_hab`.",
    )

    ipp_hab = numeric_series["ipp_pesos_hab"]
    ipp_inf = int(ipp_hab.isin([float("inf"), float("-inf")]).sum())
    _append_final_check(
        checks,
        "ipp_pesos_hab_sin_inf",
        "`ipp_pesos_hab` no contiene infinitos.",
        ipp_inf == 0,
        ipp_inf,
        0,
        "Sin infinitos en IPP por habitante."
        if ipp_inf == 0
        else "Se detectaron infinitos en `ipp_pesos_hab`.",
    )

    null_counts = {column: int(dataframe[column].isna().sum()) for column in dataframe.columns}
    key_checks_ok = all(
        check.is_valid
        for check in checks
        if check.check_id
        in {
            "columnas_esperadas",
            "fila_por_comuna",
            "codigo_comuna_no_nulo",
            "codigo_comuna_formato",
            "codigo_comuna_unico",
            "cantidad_comunas",
            "cobertura_dim_base",
            "nombre_comuna_base",
            "convertibilidad_numerica",
            "anios_referencia",
            "poblacion_positiva",
            "pobreza_rango",
            "areas_verdes_no_negativas",
            "ipp_no_negativo",
            "areas_verdes_m2_hab_sin_inf",
            "ipp_pesos_hab_sin_inf",
        }
    )
    _append_final_check(
        checks,
        "apto_para_sqlite",
        "El dataset final es apto para pasar a Fase 8 / carga a SQLite.",
        key_checks_ok,
        "APTO" if key_checks_ok else "NO APTO",
        "APTO",
        "El dataset final cumple los criterios estructurales y de integridad requeridos."
        if key_checks_ok
        else "Persisten errores de estructura, llave o rangos que deben resolverse antes de Fase 8.",
    )

    summary_row = {
        "dataset_path": _relpath(dataset_path),
        "filas": len(dataframe),
        "columnas": len(dataframe.columns),
        "codigo_comuna_unicos": int(normalized_codes.nunique(dropna=True)),
        "codigo_comuna_nulos": codigo_nulls,
        "missing_codes": " | ".join(missing_codes),
        "extra_codes": " | ".join(extra_codes),
        "errores_convertibilidad": sum(numeric_convertibility_errors.values()),
        "apto_para_sqlite": "SI" if key_checks_ok else "NO",
        "estado": "OK" if key_checks_ok else "ERROR",
    }

    return FinalDatasetValidationResult(
        dataset_path=_relpath(dataset_path),
        row_count=len(dataframe),
        column_count=len(dataframe.columns),
        is_valid=key_checks_ok,
        checks=tuple(checks),
        null_counts=null_counts,
        numeric_convertibility_errors=numeric_convertibility_errors,
        missing_codes=missing_codes,
        extra_codes=extra_codes,
        summary_row=summary_row,
    )


def export_final_validation_csv(
    validation_result: FinalDatasetValidationResult,
    path: Path = REPORTE_VALIDACION_FINAL_CSV_PATH,
) -> pd.DataFrame:
    ensure_directories()
    rows: list[dict[str, object]] = []

    for check in validation_result.checks:
        rows.append(
            {
                "categoria": "check",
                "check_id": check.check_id,
                "descripcion": check.description,
                "resultado": check.status_label,
                "valor_observado": check.observed_value,
                "criterio": check.expected_value,
                "detalle": check.detail,
            }
        )

    for column, null_count in validation_result.null_counts.items():
        rows.append(
            {
                "categoria": "null_count",
                "check_id": f"nulos_{column}",
                "descripcion": f"Nulos observados en `{column}`.",
                "resultado": "INFO",
                "valor_observado": null_count,
                "criterio": "conteo >= 0",
                "detalle": "Conteo de nulos por columna del dataset final.",
            }
        )

    for column, invalid_count in validation_result.numeric_convertibility_errors.items():
        rows.append(
            {
                "categoria": "numeric_convertibility",
                "check_id": f"convertibilidad_{column}",
                "descripcion": f"Valores no convertibles en `{column}`.",
                "resultado": "OK" if invalid_count == 0 else "ERROR",
                "valor_observado": invalid_count,
                "criterio": 0,
                "detalle": "Cantidad de celdas no nulas que no pudieron convertirse a numerico.",
            }
        )

    dataframe = pd.DataFrame(rows)
    dataframe.to_csv(path, index=False, encoding="utf-8")
    return dataframe


def build_final_validation_markdown(
    validation_result: FinalDatasetValidationResult,
    path: Path = FINAL_DATASET_PATH,
) -> str:
    lines = [
        "# Reporte de validacion final",
        "",
        "## Dataset validado",
        f"- Archivo: `{validation_result.dataset_path}`",
        f"- Filas observadas: {validation_result.row_count}",
        f"- Columnas observadas: {validation_result.column_count}",
        f"- Estado global: {'APTO PARA FASE 8' if validation_result.is_valid else 'NO APTO PARA FASE 8'}",
        "",
        "## Chequeos ejecutados",
    ]

    for check in validation_result.checks:
        lines.append(
            f"- [{check.status_label}] {check.description} "
            f"(observado: {check.observed_value}; esperado: {check.expected_value})."
        )
        lines.append(f"  {check.detail}")

    lines.extend(
        [
            "",
            "## Nulos por columna",
        ]
    )
    for column, null_count in validation_result.null_counts.items():
        lines.append(f"- `{column}`: {null_count}")

    lines.extend(
        [
            "",
            "## Convertibilidad numerica",
        ]
    )
    for column, invalid_count in validation_result.numeric_convertibility_errors.items():
        lines.append(f"- `{column}`: {invalid_count} errores de conversion")

    lines.extend(
        [
            "",
            "## Cobertura comunal",
            f"- Codigos faltantes respecto a base maestra: {list(validation_result.missing_codes)}",
            f"- Codigos extra respecto a base maestra: {list(validation_result.extra_codes)}",
            "",
            "## Observacion metodologica",
            "- Esta validacion confirma integridad estructural y consistencia descriptiva del dataset final.",
            "- El uso analitico sigue siendo comparativo y descriptivo; no habilita inferencias causales.",
        ]
    )
    return "\n".join(lines) + "\n"


def export_final_validation_markdown(
    markdown: str,
    path: Path = REPORTE_VALIDACION_FINAL_MD_PATH,
) -> None:
    ensure_directories()
    path.write_text(markdown, encoding="utf-8")


def run_phase_7_validation(
    final_df: pd.DataFrame | None = None,
    dim_base: pd.DataFrame | None = None,
    dataset_path: Path = FINAL_DATASET_PATH,
) -> dict[str, object]:
    dataframe = final_df.copy() if final_df is not None else load_final_dataset(dataset_path)
    dim_base = dim_base.copy() if dim_base is not None else pd.read_csv(dataset_path.parent.parent / "raw" / "dim_comuna_base.csv")

    validation_result = validate_final_dataset(
        final_df=dataframe,
        dim_base=dim_base,
        dataset_path=dataset_path,
    )
    validation_df = export_final_validation_csv(validation_result)
    summary_markdown = build_final_validation_markdown(validation_result, path=dataset_path)
    export_final_validation_markdown(summary_markdown)
    return {
        "validation_result": validation_result,
        "validation_df": validation_df,
        "summary_markdown": summary_markdown,
        "csv_path": REPORTE_VALIDACION_FINAL_CSV_PATH,
        "markdown_path": REPORTE_VALIDACION_FINAL_MD_PATH,
    }
