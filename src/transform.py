from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from comunas import apply_comuna_standardization, load_master_comuna_dimension
from config import (
    PROCESSED_DIR,
    PROCESSED_SOURCE_PATHS,
    SOURCE_COMUNA_KEY_COLUMNS,
    STAGING_DIR,
    STAGING_SOURCE_PATHS,
    ensure_directories,
)
from extract import SourceDataset, read_all_sources


@dataclass(frozen=True)
class TableArtifact:
    source_id: str
    path: Path
    row_count: int
    column_count: int
    columns: tuple[str, ...]


def _clean_text(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return " ".join(str(value).split())


def _coerce_int_series(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.map(_clean_text).replace("", pd.NA), errors="coerce").astype("Int64")


def _coerce_float_series(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.map(_clean_text).replace("", pd.NA), errors="coerce").astype("Float64")


def _coerce_area_component(series: pd.Series) -> pd.Series:
    cleaned = series.map(_clean_text).replace(
        {
            "": pd.NA,
            "No Recepcionado": pd.NA,
            "No Aplica": "0",
        }
    )
    return pd.to_numeric(cleaned, errors="coerce").astype("Int64")


def _scale_proportion_to_percent(series: pd.Series) -> pd.Series:
    numeric = _coerce_float_series(series)
    return (numeric * 100).round(4).astype("Float64")


def _export_csv(dataframe: pd.DataFrame, path: Path) -> TableArtifact:
    path.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(path, index=False, encoding="utf-8")
    return TableArtifact(
        source_id=path.stem,
        path=path,
        row_count=len(dataframe),
        column_count=len(dataframe.columns),
        columns=tuple(map(str, dataframe.columns)),
    )


def _build_in_scope_source_frame(
    source_id: str,
    dataset: SourceDataset,
    dim_base: pd.DataFrame,
) -> pd.DataFrame:
    source_frame = dataset.raw_df.copy()
    key_columns = SOURCE_COMUNA_KEY_COLUMNS[source_id]
    standardized = apply_comuna_standardization(
        source_frame,
        nombre_column=key_columns["nombre"],
        codigo_column=key_columns["codigo"],
    )
    standardized["nombre_comuna_fuente"] = standardized[key_columns["nombre"]].map(_clean_text)
    standardized = standardized.dropna(subset=["codigo_comuna"]).copy()
    standardized["codigo_comuna"] = standardized["codigo_comuna"].astype("Int64")

    in_scope = standardized[standardized["codigo_comuna"].isin(dim_base["codigo_comuna"])].copy()
    duplicated_codes = in_scope.loc[
        in_scope["codigo_comuna"].duplicated(keep=False),
        "codigo_comuna",
    ].dropna()
    if not duplicated_codes.empty:
        duplicates = ", ".join(map(str, duplicated_codes.astype(int).unique()))
        raise ValueError(
            f"La fuente {source_id} tiene `codigo_comuna` duplicado dentro del universo final: {duplicates}."
        )

    columns_to_drop = [key_columns["nombre"], "nombre_comuna_normalizado"]
    in_scope = in_scope.drop(columns=columns_to_drop, errors="ignore")
    merged = dim_base[["codigo_comuna", "nombre_comuna"]].merge(
        in_scope,
        on="codigo_comuna",
        how="left",
    )
    return merged.sort_values("codigo_comuna", kind="stable").reset_index(drop=True)


def _transform_source_a(dataset: SourceDataset, dim_base: pd.DataFrame) -> pd.DataFrame:
    scoped = _build_in_scope_source_frame("A", dataset, dim_base)
    transformed = pd.DataFrame(
        {
            "codigo_comuna": scoped["codigo_comuna"].astype("Int64"),
            "nombre_comuna": scoped["nombre_comuna"],
            "areas_verdes_parques_m2_2024": _coerce_area_component(scoped["mmpqc_2024"]),
            "areas_verdes_plazas_m2_2024": _coerce_area_component(scoped["mmpzc_2024"]),
        }
    )
    transformed["areas_verdes_total_m2_2024"] = transformed[
        [
            "areas_verdes_parques_m2_2024",
            "areas_verdes_plazas_m2_2024",
        ]
    ].sum(axis=1, min_count=2).astype("Int64")
    return transformed


def _transform_source_b(dataset: SourceDataset, dim_base: pd.DataFrame) -> pd.DataFrame:
    scoped = _build_in_scope_source_frame("B", dataset, dim_base)
    return pd.DataFrame(
        {
            "codigo_comuna": scoped["codigo_comuna"].astype("Int64"),
            "nombre_comuna": scoped["nombre_comuna"],
            "ipp_miles_pesos_2024": _coerce_int_series(scoped["iadm41_2024"]),
        }
    )


def _transform_source_c(dataset: SourceDataset, dim_base: pd.DataFrame) -> pd.DataFrame:
    scoped = _build_in_scope_source_frame("C", dataset, dim_base)
    return pd.DataFrame(
        {
            "codigo_comuna": scoped["codigo_comuna"].astype("Int64"),
            "nombre_comuna": scoped["nombre_comuna"],
            "personas_proyectadas_2022": _coerce_int_series(
                scoped["Número de personas según proyecciones de población (*)"]
            ),
            "personas_pobreza_ingresos_2022": _coerce_int_series(
                scoped["Número de personas en situación de pobreza por ingresos (**)"]
            ),
            "pobreza_ingresos_pct_2022": _scale_proportion_to_percent(
                scoped["Porcentaje de personas en situación de pobreza por ingresos 2022"]
            ),
            "pobreza_ingresos_pct_limite_inferior_2022": _scale_proportion_to_percent(
                scoped["Límite inferior (***)"]
            ),
            "pobreza_ingresos_pct_limite_superior_2022": _scale_proportion_to_percent(
                scoped["Límite superior"]
            ),
        }
    )


def _transform_source_d(dataset: SourceDataset, dim_base: pd.DataFrame) -> pd.DataFrame:
    scoped = _build_in_scope_source_frame("D", dataset, dim_base)
    return pd.DataFrame(
        {
            "codigo_comuna": scoped["codigo_comuna"].astype("Int64"),
            "nombre_comuna": scoped["nombre_comuna"],
            "poblacion_censada_2024": _coerce_int_series(scoped["Población censada"]),
            "hombres_2024": _coerce_int_series(scoped["Hombres"]),
            "mujeres_2024": _coerce_int_series(scoped["Mujeres"]),
            "razon_hombre_mujer_2024": _coerce_float_series(scoped["Razón hombre-mujer"]).round(1),
        }
    )


TRANSFORMERS = {
    "A": _transform_source_a,
    "B": _transform_source_b,
    "C": _transform_source_c,
    "D": _transform_source_d,
}


def export_staging_sources(
    datasets: dict[str, SourceDataset],
) -> dict[str, TableArtifact]:
    ensure_directories()
    STAGING_DIR.mkdir(parents=True, exist_ok=True)

    artifacts: dict[str, TableArtifact] = {}
    for source_id, dataset in datasets.items():
        path = STAGING_SOURCE_PATHS[source_id]
        artifact = _export_csv(dataset.raw_df, path)
        artifacts[source_id] = TableArtifact(
            source_id=source_id,
            path=artifact.path,
            row_count=artifact.row_count,
            column_count=artifact.column_count,
            columns=artifact.columns,
        )
    return artifacts


def transform_sources_to_processed(
    datasets: dict[str, SourceDataset],
    dim_base: pd.DataFrame | None = None,
) -> dict[str, pd.DataFrame]:
    dim_base = dim_base.copy() if dim_base is not None else load_master_comuna_dimension()
    return {
        source_id: TRANSFORMERS[source_id](dataset, dim_base)
        for source_id, dataset in datasets.items()
    }


def export_processed_sources(
    processed_tables: dict[str, pd.DataFrame],
) -> dict[str, TableArtifact]:
    ensure_directories()
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    artifacts: dict[str, TableArtifact] = {}
    for source_id, dataframe in processed_tables.items():
        path = PROCESSED_SOURCE_PATHS[source_id]
        artifact = _export_csv(dataframe, path)
        artifacts[source_id] = TableArtifact(
            source_id=source_id,
            path=artifact.path,
            row_count=artifact.row_count,
            column_count=artifact.column_count,
            columns=artifact.columns,
        )
    return artifacts


def run_phase_4_stage_sources(
    datasets: dict[str, SourceDataset] | None = None,
) -> dict[str, object]:
    datasets = datasets or read_all_sources()
    artifacts = export_staging_sources(datasets)
    return {
        "datasets": datasets,
        "artifacts": artifacts,
    }


def run_phase_5_transform_sources(
    datasets: dict[str, SourceDataset] | None = None,
    dim_base: pd.DataFrame | None = None,
) -> dict[str, object]:
    datasets = datasets or read_all_sources()
    dim_base = dim_base.copy() if dim_base is not None else load_master_comuna_dimension()
    processed_tables = transform_sources_to_processed(datasets, dim_base=dim_base)
    artifacts = export_processed_sources(processed_tables)
    return {
        "datasets": datasets,
        "dim_base": dim_base,
        "processed_tables": processed_tables,
        "artifacts": artifacts,
    }
