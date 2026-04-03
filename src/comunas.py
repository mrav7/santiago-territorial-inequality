from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import unicodedata

import pandas as pd

from config import (
    COMUNA_HOMOLOGACION_MANUAL,
    DIM_COMUNA_BASE_PATH,
    EXPECTED_DIM_COMUNA_ROWS,
    EXPECTED_PROVINCIA,
    EXPECTED_REGION,
    HOMOLOGACION_COMUNAS_PATH,
    OUTPUTS_DIR,
    RESUMEN_HOMOLOGACION_PATH,
    SOURCE_COMUNA_KEY_COLUMNS,
    ensure_directories,
)
from extract import SourceDataset, read_all_sources

MASTER_KEY_POLICY = (
    "La llave principal del proyecto es `codigo_comuna`. "
    "`nombre_comuna` se usa solo como apoyo descriptivo y de verificacion; "
    "no deben hacerse joins futuros por nombre crudo."
)


@dataclass(frozen=True)
class MasterDimensionValidation:
    is_valid: bool
    row_count: int
    codigo_unique: bool
    nombre_unique: bool
    provincia_values: tuple[str, ...]
    region_values: tuple[str, ...]
    statuses: tuple[str, ...]
    warnings: tuple[str, ...]


def _clean_text(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return " ".join(str(value).split())


def _auto_normalize_comuna_name(value: object) -> str:
    text = _clean_text(value).upper()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^A-Z0-9]+", " ", text)
    return " ".join(text.split())


def _normalize_manual_map(manual_map: dict[str, str] | None = None) -> dict[str, str]:
    manual_map = manual_map or COMUNA_HOMOLOGACION_MANUAL
    return {
        _auto_normalize_comuna_name(source): _auto_normalize_comuna_name(target)
        for source, target in manual_map.items()
    }


def normalize_comuna_name(value: object, manual_map: dict[str, str] | None = None) -> str:
    normalized = _auto_normalize_comuna_name(value)
    return _normalize_manual_map(manual_map).get(normalized, normalized)


def normalize_comuna_series(
    series: pd.Series,
    manual_map: dict[str, str] | None = None,
) -> pd.Series:
    normalized_map = _normalize_manual_map(manual_map)
    return series.map(
        lambda value: normalized_map.get(
            _auto_normalize_comuna_name(value),
            _auto_normalize_comuna_name(value),
        )
    )


def apply_comuna_standardization(
    dataframe: pd.DataFrame,
    nombre_column: str,
    codigo_column: str | None = None,
    manual_map: dict[str, str] | None = None,
) -> pd.DataFrame:
    standardized = dataframe.copy()
    standardized["nombre_comuna_normalizado"] = normalize_comuna_series(
        standardized[nombre_column],
        manual_map=manual_map,
    )
    if codigo_column is not None and codigo_column in standardized.columns:
        standardized["codigo_comuna"] = pd.to_numeric(
            standardized[codigo_column],
            errors="coerce",
        ).astype("Int64")
    return standardized


def load_master_comuna_dimension(path: Path = DIM_COMUNA_BASE_PATH) -> pd.DataFrame:
    dim_base = pd.read_csv(path, dtype={"codigo_comuna": "Int64"})
    dim_base["nombre_normalizado"] = normalize_comuna_series(dim_base["nombre_comuna"])
    return dim_base


def validate_master_comuna_dimension(dim_base: pd.DataFrame | None = None) -> MasterDimensionValidation:
    dim_base = dim_base.copy() if dim_base is not None else load_master_comuna_dimension()

    statuses: list[str] = []
    warnings: list[str] = []

    row_count = len(dim_base)
    codigo_unique = bool(dim_base["codigo_comuna"].is_unique)
    nombre_unique = bool(dim_base["nombre_comuna"].is_unique)
    provincia_values = tuple(sorted(dim_base["provincia"].dropna().astype(str).unique()))
    region_values = tuple(sorted(dim_base["region"].dropna().astype(str).unique()))

    if row_count == EXPECTED_DIM_COMUNA_ROWS:
        statuses.append(
            f"[OK] La dimension maestra contiene {EXPECTED_DIM_COMUNA_ROWS} comunas."
        )
    else:
        statuses.append(
            f"[ERROR] La dimension maestra contiene {row_count} filas; se esperaban {EXPECTED_DIM_COMUNA_ROWS}."
        )

    if codigo_unique:
        statuses.append("[OK] `codigo_comuna` es unico en la dimension maestra.")
    else:
        statuses.append("[ERROR] `codigo_comuna` presenta duplicados en la dimension maestra.")

    if nombre_unique:
        statuses.append("[OK] `nombre_comuna` es unico en la dimension maestra.")
    else:
        statuses.append("[ERROR] `nombre_comuna` presenta duplicados en la dimension maestra.")

    if provincia_values == (EXPECTED_PROVINCIA,):
        statuses.append(
            f"[OK] La provincia es coherente con el alcance final: {EXPECTED_PROVINCIA}."
        )
    else:
        statuses.append(
            f"[ERROR] La provincia contiene valores no esperados: {provincia_values}."
        )

    if region_values == (EXPECTED_REGION,):
        statuses.append(
            f"[OK] La region es coherente con el alcance final: {EXPECTED_REGION}."
        )
    else:
        statuses.append(
            f"[ERROR] La region contiene valores no esperados: {region_values}."
        )

    if dim_base["fuente_referencia"].isna().any():
        warnings.append(
            "La dimension maestra tiene `fuente_referencia` nulo en al menos una fila."
        )

    is_valid = (
        row_count == EXPECTED_DIM_COMUNA_ROWS
        and codigo_unique
        and nombre_unique
        and provincia_values == (EXPECTED_PROVINCIA,)
        and region_values == (EXPECTED_REGION,)
    )

    return MasterDimensionValidation(
        is_valid=is_valid,
        row_count=row_count,
        codigo_unique=codigo_unique,
        nombre_unique=nombre_unique,
        provincia_values=provincia_values,
        region_values=region_values,
        statuses=tuple(statuses),
        warnings=tuple(warnings),
    )


def _get_source_key_columns(source_id: str) -> tuple[str, str]:
    key_columns = SOURCE_COMUNA_KEY_COLUMNS[source_id]
    return key_columns["codigo"], key_columns["nombre"]


def _prepare_source_key_view(
    source_id: str,
    dataset: SourceDataset,
    manual_map: dict[str, str] | None = None,
) -> pd.DataFrame:
    codigo_column, nombre_column = _get_source_key_columns(source_id)
    standardized = apply_comuna_standardization(
        dataset.dataframe,
        nombre_column=nombre_column,
        codigo_column=codigo_column,
        manual_map=manual_map,
    )
    standardized["fuente"] = source_id
    standardized["nombre_fuente"] = standardized[nombre_column].map(_clean_text)
    standardized["nombre_normalizado"] = standardized["nombre_comuna_normalizado"]
    standardized["codigo_comuna"] = standardized["codigo_comuna"].astype("Int64")

    return standardized[
        [
            "fuente",
            "codigo_comuna",
            "nombre_fuente",
            "nombre_normalizado",
        ]
    ].dropna(subset=["codigo_comuna"])


def _classify_homologation_row(
    row: pd.Series,
    normalized_manual_map: dict[str, str],
) -> tuple[str, bool, str]:
    if pd.isna(row["nombre_comuna_base"]):
        return (
            "fuera_de_alcance",
            False,
            "Codigo comunal presente en la fuente, pero fuera del universo final de 32 comunas.",
        )

    if row["nombre_fuente"] == row["nombre_comuna_base"]:
        return (
            "coincidencia_exacta",
            False,
            "La fuente coincide exactamente con la base maestra por codigo y nombre.",
        )

    auto_normalized = _auto_normalize_comuna_name(row["nombre_fuente"])
    if row["nombre_normalizado"] == row["nombre_normalizado_base"]:
        if normalized_manual_map.get(auto_normalized) == row["nombre_normalizado"]:
            return (
                "coincidencia_por_homologacion_manual",
                False,
                "La fuente se alinea con la base maestra mediante el diccionario manual de homologacion.",
            )
        return (
            "coincidencia_por_normalizacion",
            False,
            "La diferencia de nombre se resuelve automaticamente con normalizacion de mayusculas, espacios y tildes.",
        )

    return (
        "requiere_homologacion_manual",
        True,
        "La fuente no coincide con la base maestra tras la normalizacion automatica y requiere revision manual.",
    )


def build_homologation_table(
    datasets: dict[str, SourceDataset] | None = None,
    dim_base: pd.DataFrame | None = None,
    manual_map: dict[str, str] | None = None,
) -> pd.DataFrame:
    datasets = datasets or read_all_sources()
    dim_base = dim_base.copy() if dim_base is not None else load_master_comuna_dimension()
    normalized_manual_map = _normalize_manual_map(manual_map)

    rows: list[pd.DataFrame] = []
    for source_id, dataset in datasets.items():
        source_view = _prepare_source_key_view(
            source_id,
            dataset,
            manual_map=manual_map,
        )
        merged = source_view.merge(
            dim_base[
                [
                    "codigo_comuna",
                    "nombre_comuna",
                    "nombre_normalizado",
                ]
            ].rename(
                columns={
                    "nombre_comuna": "nombre_comuna_base",
                    "nombre_normalizado": "nombre_normalizado_base",
                }
            ),
            on="codigo_comuna",
            how="left",
        )
        merged["tipo_diferencia"] = ""
        merged["requiere_homologacion_manual"] = False
        merged["observacion"] = ""
        for index, row in merged.iterrows():
            tipo_diferencia, requiere_manual, observacion = _classify_homologation_row(
                row,
                normalized_manual_map=normalized_manual_map,
            )
            merged.at[index, "tipo_diferencia"] = tipo_diferencia
            merged.at[index, "requiere_homologacion_manual"] = requiere_manual
            merged.at[index, "observacion"] = observacion
        merged["llave_principal_proyecto"] = "codigo_comuna"
        rows.append(merged)

    homologation_df = pd.concat(rows, ignore_index=True)
    homologation_df["requiere_homologacion_manual"] = homologation_df[
        "requiere_homologacion_manual"
    ].astype(bool)
    return homologation_df[
        [
            "fuente",
            "codigo_comuna",
            "nombre_comuna_base",
            "nombre_fuente",
            "nombre_normalizado",
            "tipo_diferencia",
            "requiere_homologacion_manual",
            "observacion",
            "llave_principal_proyecto",
        ]
    ].sort_values(["fuente", "codigo_comuna"], kind="stable").reset_index(drop=True)


def _build_homologation_summary(
    homologation_df: pd.DataFrame,
    validation: MasterDimensionValidation,
) -> tuple[str, pd.DataFrame]:
    summary_rows: list[dict[str, object]] = []
    for source_id, source_df in homologation_df.groupby("fuente", sort=True):
        summary_rows.append(
            {
                "fuente": source_id,
                "registros_fuente": len(source_df),
                "dentro_universo_final": int(
                    (source_df["tipo_diferencia"] != "fuera_de_alcance").sum()
                ),
                "fuera_universo_final": int(
                    (source_df["tipo_diferencia"] == "fuera_de_alcance").sum()
                ),
                "coincidencias_exactas": int(
                    (source_df["tipo_diferencia"] == "coincidencia_exacta").sum()
                ),
                "coincidencias_por_normalizacion": int(
                    (source_df["tipo_diferencia"] == "coincidencia_por_normalizacion").sum()
                ),
                "coincidencias_por_homologacion_manual": int(
                    (source_df["tipo_diferencia"] == "coincidencia_por_homologacion_manual").sum()
                ),
                "requieren_homologacion_manual": int(
                    source_df["requiere_homologacion_manual"].sum()
                ),
                "diferencias_totales_nombre": int(
                    source_df["tipo_diferencia"].isin(
                        {
                            "coincidencia_por_normalizacion",
                            "coincidencia_por_homologacion_manual",
                            "requiere_homologacion_manual",
                        }
                    ).sum()
                ),
            }
        )

    summary_df = pd.DataFrame(summary_rows).sort_values("fuente", kind="stable")

    lines = [
        "# Resumen de homologacion comunal",
        "",
        "## Base maestra validada",
        f"- Filas esperadas: {EXPECTED_DIM_COMUNA_ROWS}; filas observadas: {validation.row_count}.",
        f"- `codigo_comuna` unico: {'si' if validation.codigo_unique else 'no'}.",
        f"- `nombre_comuna` unico: {'si' if validation.nombre_unique else 'no'}.",
        f"- Provincia observada: {', '.join(validation.provincia_values)}.",
        f"- Region observada: {', '.join(validation.region_values)}.",
        f"- Criterio operativo: {MASTER_KEY_POLICY}",
        "",
        "## Resultados por fuente",
    ]

    for row in summary_df.to_dict(orient="records"):
        lines.append(
            f"- Fuente {row['fuente']}: {row['registros_fuente']} codigos validos; "
            f"{row['dentro_universo_final']} dentro del universo final y "
            f"{row['fuera_universo_final']} fuera de alcance."
        )
        lines.append(
            f"  Coincidencias exactas={row['coincidencias_exactas']}; "
            f"por normalizacion={row['coincidencias_por_normalizacion']}; "
            f"por homologacion manual={row['coincidencias_por_homologacion_manual']}; "
            f"manuales pendientes={row['requieren_homologacion_manual']}."
        )

    lines.extend(
        [
            "",
            "## Recomendacion operativa",
            "- Todos los merges futuros deben hacerse por `codigo_comuna`.",
            "- `nombre_comuna` debe mantenerse solo para verificaciones, trazabilidad y presentacion.",
            "- Los registros `fuera_de_alcance` no deben entrar al dataset final de la Provincia de Santiago.",
        ]
    )

    pending_manual = int(summary_df["requieren_homologacion_manual"].sum()) if not summary_df.empty else 0
    if pending_manual:
        lines.append(
            f"- Quedan {pending_manual} casos con homologacion manual pendiente antes de integrar."
        )
    else:
        lines.append(
            "- No quedan casos con homologacion manual pendiente dentro del universo final."
        )

    return "\n".join(lines) + "\n", summary_df


def export_homologation_outputs(
    homologation_df: pd.DataFrame,
    summary_markdown: str,
    homologation_path: Path = HOMOLOGACION_COMUNAS_PATH,
    summary_path: Path = RESUMEN_HOMOLOGACION_PATH,
) -> None:
    homologation_df.to_csv(homologation_path, index=False, encoding="utf-8")
    summary_path.write_text(summary_markdown, encoding="utf-8")


def run_phase_3_master_key(
    datasets: dict[str, SourceDataset] | None = None,
    manual_map: dict[str, str] | None = None,
) -> dict[str, object]:
    ensure_directories()
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    datasets = datasets or read_all_sources()
    dim_base = load_master_comuna_dimension()
    validation = validate_master_comuna_dimension(dim_base)
    if not validation.is_valid:
        raise ValueError("La dimension maestra comunal no es apta para Fase 3.")

    homologation_df = build_homologation_table(
        datasets=datasets,
        dim_base=dim_base,
        manual_map=manual_map,
    )
    summary_markdown, summary_df = _build_homologation_summary(
        homologation_df=homologation_df,
        validation=validation,
    )
    export_homologation_outputs(
        homologation_df=homologation_df,
        summary_markdown=summary_markdown,
    )

    return {
        "master_dimension": dim_base,
        "validation": validation,
        "homologation_df": homologation_df,
        "summary_df": summary_df,
        "summary_markdown": summary_markdown,
        "master_key_policy": MASTER_KEY_POLICY,
        "homologation_output_path": HOMOLOGACION_COMUNAS_PATH,
        "summary_output_path": RESUMEN_HOMOLOGACION_PATH,
    }
