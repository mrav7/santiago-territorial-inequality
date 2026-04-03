from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from comunas import apply_comuna_standardization, load_master_comuna_dimension
from config import (
    SOURCE_COMUNA_KEY_COLUMNS,
    STAGING_DIR,
    STAGING_SOURCE_PATHS,
    ensure_directories,
)
from extract import SourceDataset, read_all_sources


@dataclass(frozen=True)
class StagingArtifact:
    source_id: str
    nombre_fuente: str
    path: Path
    row_count: int
    column_count: int
    columns: tuple[str, ...]


@dataclass(frozen=True)
class TransformationEvidence:
    source_id: str
    nombre_fuente: str
    raw_path: str
    archivo_logico: str
    staging_path: str
    filas_antes: int
    filas_despues: int
    fuera_de_universo_detectados: int
    filas_sin_codigo_excluidas: int
    duplicados_codigo_comuna: int
    columnas_originales_consideradas: tuple[str, ...]
    columnas_finales: tuple[str, ...]
    renombres_realizados: tuple[str, ...]
    tipos_convertidos: tuple[str, ...]
    valores_especiales_tratados: tuple[str, ...]
    filtros_aplicados: tuple[str, ...]
    observaciones: tuple[str, ...]


def _clean_text(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return " ".join(str(value).split())


def _to_numeric_code(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.map(_clean_text).replace("", pd.NA), errors="coerce").astype("Int64")


def _format_codigo_comuna(series: pd.Series) -> pd.Series:
    numeric = _to_numeric_code(series)
    return numeric.map(lambda value: f"{int(value):05d}" if pd.notna(value) else pd.NA).astype("string")


def _to_int(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.map(_clean_text).replace("", pd.NA), errors="coerce").astype("Int64")


def _to_float(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.map(_clean_text).replace("", pd.NA), errors="coerce").astype("Float64")


def _prepare_source_frame(
    source_id: str,
    dataset: SourceDataset,
    dim_base: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, int]]:
    key_columns = SOURCE_COMUNA_KEY_COLUMNS[source_id]
    frame = dataset.raw_df.copy()
    standardized = apply_comuna_standardization(
        frame,
        nombre_column=key_columns["nombre"],
        codigo_column=key_columns["codigo"],
    )
    standardized["codigo_comuna_num"] = standardized["codigo_comuna"].astype("Int64")
    standardized["nombre_comuna_fuente"] = standardized[key_columns["nombre"]].map(_clean_text)

    filas_antes = len(standardized)
    filas_sin_codigo = int(standardized["codigo_comuna_num"].isna().sum())

    valid_codes = standardized["codigo_comuna_num"].dropna()
    universe_codes = set(dim_base["codigo_comuna"].dropna().astype(int))
    fuera_de_universo = int((~valid_codes.astype(int).isin(universe_codes)).sum())

    scoped = standardized[standardized["codigo_comuna_num"].isin(dim_base["codigo_comuna"])].copy()
    duplicados = int(scoped["codigo_comuna_num"].duplicated().sum())
    scoped = scoped.merge(
        dim_base[["codigo_comuna", "nombre_comuna"]].rename(
            columns={
                "codigo_comuna": "codigo_comuna_num",
                "nombre_comuna": "nombre_comuna_estandar",
            }
        ),
        on="codigo_comuna_num",
        how="left",
    )
    scoped["codigo_comuna"] = _format_codigo_comuna(scoped["codigo_comuna_num"])
    scoped["nombre_comuna"] = scoped["nombre_comuna_estandar"]
    scoped = scoped.sort_values("codigo_comuna_num", kind="stable").reset_index(drop=True)

    stats = {
        "filas_antes": filas_antes,
        "filas_despues": len(scoped),
        "fuera_de_universo_detectados": fuera_de_universo,
        "filas_sin_codigo_excluidas": filas_sin_codigo,
        "duplicados_codigo_comuna": duplicados,
    }
    return scoped, stats


def transform_areas_verdes(
    dataset: SourceDataset,
    dim_base: pd.DataFrame,
) -> tuple[pd.DataFrame, TransformationEvidence]:
    scoped, stats = _prepare_source_frame("A", dataset, dim_base)

    parques = scoped["mmpqc_2024"].map(_clean_text)
    plazas = scoped["mmpzc_2024"].map(_clean_text)
    mmpqc = pd.to_numeric(
        parques.replace({"": pd.NA, "No Aplica": "0", "No Recepcionado": pd.NA}),
        errors="coerce",
    ).astype("Int64")
    mmpzc = pd.to_numeric(
        plazas.replace({"": pd.NA, "No Aplica": "0", "No Recepcionado": pd.NA}),
        errors="coerce",
    ).astype("Int64")

    transformed = pd.DataFrame(
        {
            "codigo_comuna": scoped["codigo_comuna"],
            "nombre_comuna": scoped["nombre_comuna"],
            "mmpqc_2024": mmpqc,
            "mmpzc_2024": mmpzc,
        }
    )
    transformed["areas_verdes_m2"] = transformed[["mmpqc_2024", "mmpzc_2024"]].sum(
        axis=1,
        min_count=2,
    ).astype("Int64")

    evidence = TransformationEvidence(
        source_id="A",
        nombre_fuente=dataset.contract.nombre_fuente,
        raw_path=dataset.contract.archivo_origen,
        archivo_logico=dataset.contract.archivo_logico,
        staging_path=STAGING_SOURCE_PATHS["A"].relative_to(STAGING_DIR.parent.parent).as_posix(),
        filas_antes=stats["filas_antes"],
        filas_despues=stats["filas_despues"],
        fuera_de_universo_detectados=stats["fuera_de_universo_detectados"],
        filas_sin_codigo_excluidas=stats["filas_sin_codigo_excluidas"],
        duplicados_codigo_comuna=stats["duplicados_codigo_comuna"],
        columnas_originales_consideradas=(
            "codigo_comuna",
            "nombre_comuna",
            "mmpqc_2024",
            "mmpzc_2024",
        ),
        columnas_finales=tuple(transformed.columns),
        renombres_realizados=("Sin renombre en columnas base; se crea `areas_verdes_m2`.",),
        tipos_convertidos=(
            "`codigo_comuna` -> string de 5 digitos.",
            "`mmpqc_2024` -> Int64.",
            "`mmpzc_2024` -> Int64.",
            "`areas_verdes_m2` -> Int64.",
        ),
        valores_especiales_tratados=(
            "`No Aplica` -> 0 en componentes de areas verdes.",
            "`No Recepcionado` -> NaN.",
        ),
        filtros_aplicados=(
            "Filtrado al universo final usando `dim_comuna_base.csv` y `codigo_comuna`.",
            "Exclusion de registros sin codigo comunal valido.",
            "Estandarizacion de `nombre_comuna` contra la dimension maestra.",
        ),
        observaciones=(
            "La suma total exige ambas componentes numericas; si una queda nula, `areas_verdes_m2` permanece nulo.",
        ),
    )
    return transformed, evidence


def transform_capacidad_municipal(
    dataset: SourceDataset,
    dim_base: pd.DataFrame,
) -> tuple[pd.DataFrame, TransformationEvidence]:
    scoped, stats = _prepare_source_frame("B", dataset, dim_base)

    transformed = pd.DataFrame(
        {
            "codigo_comuna": scoped["codigo_comuna"],
            "nombre_comuna": scoped["nombre_comuna"],
            "ipp_miles_pesos": _to_int(scoped["iadm41_2024"]),
        }
    )

    evidence = TransformationEvidence(
        source_id="B",
        nombre_fuente=dataset.contract.nombre_fuente,
        raw_path=dataset.contract.archivo_origen,
        archivo_logico=dataset.contract.archivo_logico,
        staging_path=STAGING_SOURCE_PATHS["B"].relative_to(STAGING_DIR.parent.parent).as_posix(),
        filas_antes=stats["filas_antes"],
        filas_despues=stats["filas_despues"],
        fuera_de_universo_detectados=stats["fuera_de_universo_detectados"],
        filas_sin_codigo_excluidas=stats["filas_sin_codigo_excluidas"],
        duplicados_codigo_comuna=stats["duplicados_codigo_comuna"],
        columnas_originales_consideradas=(
            "codigo_comuna",
            "nombre_comuna",
            "iadm41_2024",
        ),
        columnas_finales=tuple(transformed.columns),
        renombres_realizados=("`iadm41_2024` -> `ipp_miles_pesos`.",),
        tipos_convertidos=(
            "`codigo_comuna` -> string de 5 digitos.",
            "`ipp_miles_pesos` -> Int64.",
        ),
        valores_especiales_tratados=(
            "No se detectaron valores especiales dentro del universo final en la variable IPP.",
        ),
        filtros_aplicados=(
            "Filtrado al universo final usando `dim_comuna_base.csv` y `codigo_comuna`.",
            "Exclusion de registros sin codigo comunal valido.",
            "Estandarizacion de `nombre_comuna` contra la dimension maestra.",
        ),
        observaciones=(
            "La unidad se conserva como miles de pesos nominales 2024, consistente con metadata y el descriptor del archivo.",
        ),
    )
    return transformed, evidence


def transform_pobreza_ingresos(
    dataset: SourceDataset,
    dim_base: pd.DataFrame,
) -> tuple[pd.DataFrame, TransformationEvidence]:
    scoped, stats = _prepare_source_frame("C", dataset, dim_base)

    transformed = pd.DataFrame(
        {
            "codigo_comuna": scoped["codigo_comuna"],
            "nombre_comuna": scoped["nombre_comuna"],
            "pobreza_ingresos_pct": (_to_float(
                scoped["Porcentaje de personas en situación de pobreza por ingresos 2022"]
            ) * 100).round(4).astype("Float64"),
        }
    )

    evidence = TransformationEvidence(
        source_id="C",
        nombre_fuente=dataset.contract.nombre_fuente,
        raw_path=dataset.contract.archivo_origen,
        archivo_logico=dataset.contract.archivo_logico,
        staging_path=STAGING_SOURCE_PATHS["C"].relative_to(STAGING_DIR.parent.parent).as_posix(),
        filas_antes=stats["filas_antes"],
        filas_despues=stats["filas_despues"],
        fuera_de_universo_detectados=stats["fuera_de_universo_detectados"],
        filas_sin_codigo_excluidas=stats["filas_sin_codigo_excluidas"],
        duplicados_codigo_comuna=stats["duplicados_codigo_comuna"],
        columnas_originales_consideradas=(
            "Código",
            "Nombre comuna",
            "Porcentaje de personas en situación de pobreza por ingresos 2022",
        ),
        columnas_finales=tuple(transformed.columns),
        renombres_realizados=(
            "`Código` -> `codigo_comuna`.",
            "`Nombre comuna` -> `nombre_comuna`.",
            "`Porcentaje de personas en situación de pobreza por ingresos 2022` -> `pobreza_ingresos_pct`.",
        ),
        tipos_convertidos=(
            "`codigo_comuna` -> string de 5 digitos.",
            "`pobreza_ingresos_pct` -> Float64 en escala 0-100.",
        ),
        valores_especiales_tratados=(
            "Se excluyen filas de nota, blancos y residuos textuales al exigir `codigo_comuna` valido.",
        ),
        filtros_aplicados=(
            "Exclusion de filas sin codigo comunal valido.",
            "Filtrado al universo final usando `dim_comuna_base.csv` y `codigo_comuna`.",
            "Estandarizacion de `nombre_comuna` contra la dimension maestra.",
        ),
        observaciones=(
            "La variable original venia como proporcion 0-1 y se transformo a porcentaje 0-100.",
        ),
    )
    return transformed, evidence


def transform_poblacion(
    dataset: SourceDataset,
    dim_base: pd.DataFrame,
) -> tuple[pd.DataFrame, TransformationEvidence]:
    scoped, stats = _prepare_source_frame("D", dataset, dim_base)

    transformed = pd.DataFrame(
        {
            "codigo_comuna": scoped["codigo_comuna"],
            "nombre_comuna": scoped["nombre_comuna"],
            "poblacion": _to_int(scoped["Población censada"]),
        }
    )

    evidence = TransformationEvidence(
        source_id="D",
        nombre_fuente=dataset.contract.nombre_fuente,
        raw_path=dataset.contract.archivo_origen,
        archivo_logico=dataset.contract.archivo_logico,
        staging_path=STAGING_SOURCE_PATHS["D"].relative_to(STAGING_DIR.parent.parent).as_posix(),
        filas_antes=stats["filas_antes"],
        filas_despues=stats["filas_despues"],
        fuera_de_universo_detectados=stats["fuera_de_universo_detectados"],
        filas_sin_codigo_excluidas=stats["filas_sin_codigo_excluidas"],
        duplicados_codigo_comuna=stats["duplicados_codigo_comuna"],
        columnas_originales_consideradas=(
            "Código comuna",
            "Comuna",
            "Población censada",
        ),
        columnas_finales=tuple(transformed.columns),
        renombres_realizados=(
            "`Código comuna` -> `codigo_comuna`.",
            "`Comuna` -> `nombre_comuna`.",
            "`Población censada` -> `poblacion`.",
        ),
        tipos_convertidos=(
            "`codigo_comuna` -> string de 5 digitos.",
            "`poblacion` -> Int64.",
        ),
        valores_especiales_tratados=(
            "Se excluyen la fila agregada `País`, filas en blanco y notas al exigir `codigo_comuna` valido y filtrar por el universo final.",
        ),
        filtros_aplicados=(
            "Exclusion de filas sin codigo comunal valido.",
            "Filtrado al universo final usando `dim_comuna_base.csv` y `codigo_comuna`.",
            "Estandarizacion de `nombre_comuna` contra la dimension maestra.",
        ),
        observaciones=(
            "La fuente original contiene columnas adicionales de sexo y razon hombre-mujer, pero en esta fase solo se conserva `poblacion`.",
        ),
    )
    return transformed, evidence


TRANSFORM_FUNCTIONS = {
    "A": transform_areas_verdes,
    "B": transform_capacidad_municipal,
    "C": transform_pobreza_ingresos,
    "D": transform_poblacion,
}


def _write_staging_csv(dataframe: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(path, index=False, encoding="utf-8")


def extract_all_to_staging(
    datasets: dict[str, SourceDataset] | None = None,
    dim_base: pd.DataFrame | None = None,
) -> dict[str, object]:
    ensure_directories()
    STAGING_DIR.mkdir(parents=True, exist_ok=True)

    datasets = datasets or read_all_sources()
    dim_base = dim_base.copy() if dim_base is not None else load_master_comuna_dimension()

    staging_tables: dict[str, pd.DataFrame] = {}
    artifacts: dict[str, StagingArtifact] = {}
    evidences: dict[str, TransformationEvidence] = {}

    for source_id, dataset in datasets.items():
        transformed, evidence = TRANSFORM_FUNCTIONS[source_id](dataset, dim_base)
        path = STAGING_SOURCE_PATHS[source_id]
        _write_staging_csv(transformed, path)

        staging_tables[source_id] = transformed
        evidences[source_id] = evidence
        artifacts[source_id] = StagingArtifact(
            source_id=source_id,
            nombre_fuente=dataset.contract.nombre_fuente,
            path=path,
            row_count=len(transformed),
            column_count=len(transformed.columns),
            columns=tuple(map(str, transformed.columns)),
        )

    return {
        "datasets": datasets,
        "dim_base": dim_base,
        "staging_tables": staging_tables,
        "artifacts": artifacts,
        "evidences": evidences,
    }
