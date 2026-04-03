from __future__ import annotations

import os
import sqlite3
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-lab1-bi")

import matplotlib
import pandas as pd

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from config import (
    ANALISIS_EXPLORATORIO_MD_PATH,
    AREAS_VERDES_BOTTOM10_FIGURE_PATH,
    BASE_DIR,
    FINAL_DATASET_PATH,
    FIGURES_DIR,
    INDICE_REZAGO_TERRITORIAL_CSV_PATH,
    INDICE_REZAGO_TOP10_FIGURE_PATH,
    IPP_BOTTOM10_FIGURE_PATH,
    POBREZA_AREAS_SCATTER_FIGURE_PATH,
    POBREZA_TOP10_FIGURE_PATH,
    RANKING_AREAS_VERDES_CSV_PATH,
    RANKING_IPP_CSV_PATH,
    RANKING_POBREZA_CSV_PATH,
    SQLITE_PATH,
    TABLAS_HALLAZGOS_FASE9_CSV_PATH,
    ensure_directories,
)
from load import prepare_final_dataset
from validate import load_final_dataset, run_phase_7_validation

TOP_N = 5
GRAPH_TOP_N = 10
CONSISTENCY_NUMERIC_COLUMNS = (
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
HALLAZGO_EXPORT_COLUMNS = (
    "codigo_comuna",
    "nombre_comuna",
    "poblacion",
    "pobreza_ingresos_pct",
    "areas_verdes_m2_hab",
    "ipp_pesos_hab",
    "quintil_rezago_areas_verdes",
    "quintil_rezago_pobreza",
    "quintil_rezago_ipp",
    "dimensiones_rezago_critico",
    "indice_rezago_territorial",
)


def _relpath(path: Path) -> str:
    return path.relative_to(BASE_DIR).as_posix()


def _format_float(value: object, decimals: int = 4) -> str:
    if pd.isna(value):
        return "NA"
    return f"{float(value):.{decimals}f}"


def _format_name_list(dataframe: pd.DataFrame) -> str:
    if dataframe.empty:
        return "ninguna comuna"
    return ", ".join(dataframe["nombre_comuna"].astype(str).tolist())


def load_sqlite_analysis_view(path: Path = SQLITE_PATH) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"No existe la base SQLite requerida: {_relpath(path)}")

    query = """
        SELECT
            fact.codigo_comuna,
            dim.nombre_comuna,
            fact.poblacion,
            fact.anio_poblacion,
            fact.pobreza_ingresos_pct,
            fact.anio_pobreza,
            fact.areas_verdes_m2,
            fact.anio_areas_verdes,
            fact.ipp_miles_pesos,
            fact.anio_ingresos,
            fact.areas_verdes_m2_hab,
            fact.ipp_pesos_hab
        FROM fact_desigualdad_comunal AS fact
        INNER JOIN dim_comuna AS dim
            ON dim.codigo_comuna = fact.codigo_comuna
        ORDER BY fact.codigo_comuna
    """

    with sqlite3.connect(path) as connection:
        dataframe = pd.read_sql_query(query, connection, dtype={"codigo_comuna": "string"})

    return prepare_final_dataset(dataframe)


def validate_csv_sqlite_consistency(
    csv_df: pd.DataFrame,
    sqlite_df: pd.DataFrame,
) -> dict[str, object]:
    canonical_df = prepare_final_dataset(csv_df)
    persisted_df = prepare_final_dataset(sqlite_df)

    canonical_df = canonical_df.sort_values("codigo_comuna").reset_index(drop=True)
    persisted_df = persisted_df.sort_values("codigo_comuna").reset_index(drop=True)

    csv_only_codes = sorted(set(canonical_df["codigo_comuna"]) - set(persisted_df["codigo_comuna"]))
    sqlite_only_codes = sorted(set(persisted_df["codigo_comuna"]) - set(canonical_df["codigo_comuna"]))

    merged = canonical_df.merge(
        persisted_df,
        on="codigo_comuna",
        how="outer",
        suffixes=("_csv", "_sqlite"),
        indicator=True,
    )

    mismatch_counts: dict[str, int] = {}
    for column in CONSISTENCY_NUMERIC_COLUMNS:
        left = pd.to_numeric(merged[f"{column}_csv"], errors="coerce")
        right = pd.to_numeric(merged[f"{column}_sqlite"], errors="coerce")
        mismatch_counts[column] = int(
            (~left.fillna(-9999999999).round(6).eq(right.fillna(-9999999999).round(6))).sum()
        )

    name_mismatches = int(
        (
            merged["nombre_comuna_csv"].astype("string").fillna("<<NA>>")
            != merged["nombre_comuna_sqlite"].astype("string").fillna("<<NA>>")
        ).sum()
    )

    is_consistent = (
        len(canonical_df) == len(persisted_df)
        and tuple(canonical_df.columns) == tuple(persisted_df.columns)
        and not csv_only_codes
        and not sqlite_only_codes
        and name_mismatches == 0
        and all(count == 0 for count in mismatch_counts.values())
        and merged["_merge"].eq("both").all()
    )

    return {
        "csv_rows": len(canonical_df),
        "sqlite_rows": len(persisted_df),
        "csv_columns": tuple(canonical_df.columns),
        "sqlite_columns": tuple(persisted_df.columns),
        "csv_only_codes": tuple(csv_only_codes),
        "sqlite_only_codes": tuple(sqlite_only_codes),
        "name_mismatches": name_mismatches,
        "numeric_mismatch_counts": mismatch_counts,
        "is_consistent": is_consistent,
    }


def _assign_rezago_quintile(
    series: pd.Series,
    *,
    lower_is_worse: bool,
) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    result = pd.Series(pd.NA, index=series.index, dtype="Int64")
    valid = numeric.dropna()
    labels = [5, 4, 3, 2, 1] if lower_is_worse else [1, 2, 3, 4, 5]
    buckets = pd.qcut(valid.rank(method="first", ascending=True), 5, labels=labels)
    result.loc[valid.index] = pd.Series(buckets.astype(int), index=valid.index).astype("Int64")
    return result


def enrich_analysis_dataset(dataframe: pd.DataFrame) -> pd.DataFrame:
    enriched = prepare_final_dataset(dataframe).copy()
    enriched["quintil_rezago_areas_verdes"] = _assign_rezago_quintile(
        enriched["areas_verdes_m2_hab"],
        lower_is_worse=True,
    )
    enriched["quintil_rezago_pobreza"] = _assign_rezago_quintile(
        enriched["pobreza_ingresos_pct"],
        lower_is_worse=False,
    )
    enriched["quintil_rezago_ipp"] = _assign_rezago_quintile(
        enriched["ipp_pesos_hab"],
        lower_is_worse=True,
    )
    enriched["dimensiones_rezago_critico"] = (
        enriched[
            [
                "quintil_rezago_areas_verdes",
                "quintil_rezago_pobreza",
                "quintil_rezago_ipp",
            ]
        ]
        .eq(5)
        .sum(axis=1)
        .astype("Int64")
    )
    enriched["indice_rezago_territorial"] = (
        enriched["quintil_rezago_areas_verdes"]
        + enriched["quintil_rezago_pobreza"]
        + enriched["quintil_rezago_ipp"]
    ).astype("Int64")
    return enriched


def _sorted_table(
    dataframe: pd.DataFrame,
    columns: list[str],
    ascending: list[bool],
    limit: int | None = None,
) -> pd.DataFrame:
    sorted_df = dataframe.sort_values(columns, ascending=ascending).reset_index(drop=True)
    if limit is not None:
        sorted_df = sorted_df.head(limit).copy()
    return sorted_df.reset_index(drop=True)


def build_rankings(enriched_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    rankings = {
        "top_5_menor_areas_verdes_m2_hab": _sorted_table(
            enriched_df,
            ["areas_verdes_m2_hab", "codigo_comuna"],
            [True, True],
            TOP_N,
        ),
        "top_5_mayor_areas_verdes_m2_hab": _sorted_table(
            enriched_df,
            ["areas_verdes_m2_hab", "codigo_comuna"],
            [False, True],
            TOP_N,
        ),
        "top_5_mayor_pobreza_ingresos_pct": _sorted_table(
            enriched_df,
            ["pobreza_ingresos_pct", "codigo_comuna"],
            [False, True],
            TOP_N,
        ),
        "top_5_menor_pobreza_ingresos_pct": _sorted_table(
            enriched_df,
            ["pobreza_ingresos_pct", "codigo_comuna"],
            [True, True],
            TOP_N,
        ),
        "top_5_menor_ipp_pesos_hab": _sorted_table(
            enriched_df,
            ["ipp_pesos_hab", "codigo_comuna"],
            [True, True],
            TOP_N,
        ),
        "top_5_mayor_ipp_pesos_hab": _sorted_table(
            enriched_df,
            ["ipp_pesos_hab", "codigo_comuna"],
            [False, True],
            TOP_N,
        ),
    }
    return rankings


def build_cross_tables(enriched_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    cross_tables = {
        "peor_quintil_pobreza_y_areas_verdes": _sorted_table(
            enriched_df[
                (enriched_df["quintil_rezago_pobreza"] == 5)
                & (enriched_df["quintil_rezago_areas_verdes"] == 5)
            ],
            ["pobreza_ingresos_pct", "areas_verdes_m2_hab", "codigo_comuna"],
            [False, True, True],
        ),
        "peor_quintil_pobreza_y_ipp": _sorted_table(
            enriched_df[
                (enriched_df["quintil_rezago_pobreza"] == 5)
                & (enriched_df["quintil_rezago_ipp"] == 5)
            ],
            ["pobreza_ingresos_pct", "ipp_pesos_hab", "codigo_comuna"],
            [False, True, True],
        ),
        "rezagadas_en_dos_o_mas_dimensiones": _sorted_table(
            enriched_df[enriched_df["dimensiones_rezago_critico"] >= 2],
            [
                "dimensiones_rezago_critico",
                "indice_rezago_territorial",
                "pobreza_ingresos_pct",
                "codigo_comuna",
            ],
            [False, False, False, True],
        ),
    }
    return cross_tables


def build_full_export_tables(enriched_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    exports = {
        "ranking_areas_verdes": _sorted_table(
            enriched_df,
            ["areas_verdes_m2_hab", "codigo_comuna"],
            [True, True],
        ),
        "ranking_pobreza": _sorted_table(
            enriched_df,
            ["pobreza_ingresos_pct", "codigo_comuna"],
            [False, True],
        ),
        "ranking_ipp": _sorted_table(
            enriched_df,
            ["ipp_pesos_hab", "codigo_comuna"],
            [True, True],
        ),
        "indice_rezago_territorial": _sorted_table(
            enriched_df,
            ["indice_rezago_territorial", "dimensiones_rezago_critico", "codigo_comuna"],
            [False, False, True],
        ),
    }

    exports["ranking_areas_verdes"].insert(
        0,
        "ranking_ascendente_areas_verdes_m2_hab",
        range(1, len(exports["ranking_areas_verdes"]) + 1),
    )
    exports["ranking_pobreza"].insert(
        0,
        "ranking_descendente_pobreza_ingresos_pct",
        range(1, len(exports["ranking_pobreza"]) + 1),
    )
    exports["ranking_ipp"].insert(
        0,
        "ranking_ascendente_ipp_pesos_hab",
        range(1, len(exports["ranking_ipp"]) + 1),
    )
    exports["indice_rezago_territorial"].insert(
        0,
        "ranking_descendente_indice_rezago_territorial",
        range(1, len(exports["indice_rezago_territorial"]) + 1),
    )
    return exports


def build_hallazgos_table(
    rankings: dict[str, pd.DataFrame],
    cross_tables: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    table_details = {
        "top_5_menor_areas_verdes_m2_hab": "Ranking ascendente por areas_verdes_m2_hab.",
        "top_5_mayor_areas_verdes_m2_hab": "Ranking descendente por areas_verdes_m2_hab.",
        "top_5_mayor_pobreza_ingresos_pct": "Ranking descendente por pobreza_ingresos_pct.",
        "top_5_menor_pobreza_ingresos_pct": "Ranking ascendente por pobreza_ingresos_pct.",
        "top_5_menor_ipp_pesos_hab": "Ranking ascendente por ipp_pesos_hab.",
        "top_5_mayor_ipp_pesos_hab": "Ranking descendente por ipp_pesos_hab.",
        "peor_quintil_pobreza_y_areas_verdes": (
            "Comunas en peor quintil simultaneo de pobreza y areas verdes por habitante."
        ),
        "peor_quintil_pobreza_y_ipp": (
            "Comunas en peor quintil simultaneo de pobreza e IPP por habitante."
        ),
        "rezagadas_en_dos_o_mas_dimensiones": (
            "Comunas con rezago critico en al menos dos de las tres dimensiones."
        ),
    }

    for table_name, dataframe in {**rankings, **cross_tables}.items():
        for order, (_, row) in enumerate(dataframe.iterrows(), start=1):
            rows.append(
                {
                    "tabla": table_name,
                    "orden": order,
                    "detalle": table_details[table_name],
                    **{column: row[column] for column in HALLAZGO_EXPORT_COLUMNS},
                }
            )

    dataframe = pd.DataFrame(rows)
    dataframe.to_csv(TABLAS_HALLAZGOS_FASE9_CSV_PATH, index=False, encoding="utf-8")
    return dataframe


def _save_barh_chart(
    dataframe: pd.DataFrame,
    *,
    value_column: str,
    title: str,
    xlabel: str,
    path: Path,
) -> None:
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(dataframe["nombre_comuna"], dataframe[value_column])
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Comuna")
    ax.grid(axis="x", alpha=0.25)
    ax.set_axisbelow(True)
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _save_scatter_chart(
    dataframe: pd.DataFrame,
    path: Path,
) -> None:
    fig, ax = plt.subplots(figsize=(8.5, 6.5))
    ax.scatter(
        dataframe["areas_verdes_m2_hab"],
        dataframe["pobreza_ingresos_pct"],
        s=35,
    )
    ax.set_xscale("log")
    ax.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:g}"))
    ax.set_title("Pobreza por ingresos y areas verdes por habitante")
    ax.set_xlabel("Areas verdes por habitante (m2, escala log)")
    ax.set_ylabel("Pobreza por ingresos (%)")
    ax.grid(True, alpha=0.25)
    ax.set_axisbelow(True)

    highlighted = dataframe[
        dataframe["nombre_comuna"].isin(["QUILICURA", "LA PINTANA", "CONCHALI"])
    ]
    offsets = {
        "QUILICURA": (-72, 8),
        "LA PINTANA": (6, 0),
        "CONCHALI": (6, -12),
    }
    for _, row in highlighted.iterrows():
        ax.annotate(
            row["nombre_comuna"],
            (row["areas_verdes_m2_hab"], row["pobreza_ingresos_pct"]),
            textcoords="offset points",
            xytext=offsets.get(str(row["nombre_comuna"]), (6, 6)),
            fontsize=8,
        )

    ax.text(
        0.02,
        0.03,
        (
            "Nota: QUILICURA se mantiene visible como caso especial.\n"
            "La escala log ayuda a evitar la compresion del resto de las comunas."
        ),
        transform=ax.transAxes,
        fontsize=8,
        va="bottom",
        bbox={"boxstyle": "round", "alpha": 0.15},
    )

    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def create_figures(
    enriched_df: pd.DataFrame,
    full_exports: dict[str, pd.DataFrame],
) -> tuple[Path, ...]:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    _save_barh_chart(
        full_exports["ranking_areas_verdes"].head(GRAPH_TOP_N),
        value_column="areas_verdes_m2_hab",
        title="10 comunas con menos areas verdes por habitante",
        xlabel="Areas verdes por habitante (m2)",
        path=AREAS_VERDES_BOTTOM10_FIGURE_PATH,
    )
    _save_barh_chart(
        full_exports["ranking_pobreza"].head(GRAPH_TOP_N),
        value_column="pobreza_ingresos_pct",
        title="10 comunas con mayor pobreza por ingresos",
        xlabel="Pobreza por ingresos (%)",
        path=POBREZA_TOP10_FIGURE_PATH,
    )
    _save_barh_chart(
        full_exports["ranking_ipp"].head(GRAPH_TOP_N),
        value_column="ipp_pesos_hab",
        title="10 comunas con menor capacidad municipal relativa",
        xlabel="IPP por habitante (pesos)",
        path=IPP_BOTTOM10_FIGURE_PATH,
    )
    _save_scatter_chart(
        enriched_df,
        path=POBREZA_AREAS_SCATTER_FIGURE_PATH,
    )
    _save_barh_chart(
        full_exports["indice_rezago_territorial"].head(GRAPH_TOP_N),
        value_column="indice_rezago_territorial",
        title="10 comunas con mayor indice auxiliar de rezago territorial",
        xlabel="Indice auxiliar de rezago (mayor = mas rezago observado)",
        path=INDICE_REZAGO_TOP10_FIGURE_PATH,
    )

    return (
        AREAS_VERDES_BOTTOM10_FIGURE_PATH,
        POBREZA_TOP10_FIGURE_PATH,
        IPP_BOTTOM10_FIGURE_PATH,
        POBREZA_AREAS_SCATTER_FIGURE_PATH,
        INDICE_REZAGO_TOP10_FIGURE_PATH,
    )


def _build_ranking_lines(
    dataframe: pd.DataFrame,
    *,
    value_column: str,
    decimals: int,
) -> list[str]:
    lines: list[str] = []
    for order, (_, row) in enumerate(dataframe.iterrows(), start=1):
        lines.append(
            f"- {order}. {row['nombre_comuna']} ({row['codigo_comuna']}): "
            f"{_format_float(row[value_column], decimals)}"
        )
    return lines


def build_analysis_markdown(
    consistency_result: dict[str, object],
    rankings: dict[str, pd.DataFrame],
    cross_tables: dict[str, pd.DataFrame],
    figure_paths: tuple[Path, ...],
) -> str:
    worst_areas = rankings["top_5_menor_areas_verdes_m2_hab"]
    best_areas = rankings["top_5_mayor_areas_verdes_m2_hab"]
    worst_pobreza = rankings["top_5_mayor_pobreza_ingresos_pct"]
    best_pobreza = rankings["top_5_menor_pobreza_ingresos_pct"]
    worst_ipp = rankings["top_5_menor_ipp_pesos_hab"]
    best_ipp = rankings["top_5_mayor_ipp_pesos_hab"]

    cross_pobreza_areas = cross_tables["peor_quintil_pobreza_y_areas_verdes"]
    cross_pobreza_ipp = cross_tables["peor_quintil_pobreza_y_ipp"]
    rezago_multiple = cross_tables["rezagadas_en_dos_o_mas_dimensiones"]

    lines = [
        "# Analisis exploratorio Fase 9",
        "",
        "## Insumos y consistencia",
        f"- Dataset canonico analizado: `{_relpath(FINAL_DATASET_PATH)}`.",
        f"- Base SQLite contrastada: `{_relpath(SQLITE_PATH)}`.",
        f"- Filas CSV vs SQLite: {consistency_result['csv_rows']} vs {consistency_result['sqlite_rows']}.",
        f"- Cobertura exclusiva CSV: {list(consistency_result['csv_only_codes'])}.",
        f"- Cobertura exclusiva SQLite: {list(consistency_result['sqlite_only_codes'])}.",
        (
            "- Consistencia global CSV/SQLite: OK."
            if consistency_result["is_consistent"]
            else "- Consistencia global CSV/SQLite: ERROR."
        ),
        "- Fuente de verdad para Fase 9: `data/processed/desigualdad_comunal_final.csv`; SQLite se usa como validacion de persistencia y consulta.",
        "",
        "## Metodologia analitica",
        "- Los rankings obligatorios se construyen con orden explicito ascendente o descendente segun el sentido de cada variable.",
        "- Para cruces de rezago se usan quintiles por variable.",
        "- `areas_verdes_m2_hab`: menor valor = peor situacion; el peor quintil se codifica como 5.",
        "- `pobreza_ingresos_pct`: mayor valor = peor situacion; el peor quintil se codifica como 5.",
        "- `ipp_pesos_hab`: menor valor = peor situacion; el peor quintil se codifica como 5.",
        "- `indice_rezago_territorial` es una construccion analitica auxiliar: suma de los tres quintiles de rezago. Mayor valor = mayor rezago relativo observado.",
        "- El analisis es descriptivo y comparativo; no permite inferir causalidad.",
        "",
        "## Notas metodologicas para comunicacion",
        "- `indice_rezago_territorial` es un apoyo descriptivo de Fase 9 y no una variable oficial de fuente.",
        "- Los hallazgos no permiten inferencias causales; solo describen patrones observados entre comunas.",
        "- QUILICURA aparece como outlier plausible en `areas_verdes_m2_hab` y debe interpretarse como caso especial al leer tablas y graficos.",
        "- El scatter de pobreza y areas verdes usa escala logaritmica en el eje X para mantener visible el resto de las comunas sin ocultar ese caso extremo.",
        "",
        "## Rankings obligatorios",
        "### Top 5 comunas con menos `areas_verdes_m2_hab` (orden ascendente)",
        *_build_ranking_lines(worst_areas, value_column="areas_verdes_m2_hab", decimals=6),
        "",
        "### Top 5 comunas con mas `areas_verdes_m2_hab` (orden descendente)",
        *_build_ranking_lines(best_areas, value_column="areas_verdes_m2_hab", decimals=6),
        "",
        "### Top 5 comunas con mayor `pobreza_ingresos_pct` (orden descendente)",
        *_build_ranking_lines(worst_pobreza, value_column="pobreza_ingresos_pct", decimals=4),
        "",
        "### Top 5 comunas con menor `pobreza_ingresos_pct` (orden ascendente)",
        *_build_ranking_lines(best_pobreza, value_column="pobreza_ingresos_pct", decimals=4),
        "",
        "### Top 5 comunas con menor `ipp_pesos_hab` (orden ascendente)",
        *_build_ranking_lines(worst_ipp, value_column="ipp_pesos_hab", decimals=6),
        "",
        "### Top 5 comunas con mayor `ipp_pesos_hab` (orden descendente)",
        *_build_ranking_lines(best_ipp, value_column="ipp_pesos_hab", decimals=6),
        "",
        "## Cruces descriptivos",
        "- Peor quintil simultaneo de pobreza y areas verdes por habitante: "
        f"{_format_name_list(cross_pobreza_areas)}.",
        "- Peor quintil simultaneo de pobreza e IPP por habitante: "
        f"{_format_name_list(cross_pobreza_ipp)}.",
        "- Rezagadas en al menos dos dimensiones: "
        f"{_format_name_list(rezago_multiple)}.",
        "",
        "## Hallazgos reutilizables",
        "- Se observa que las menores disponibilidades relativas de areas verdes se concentran en "
        f"{_format_name_list(worst_areas)}.",
        "- Las mayores tasas observadas de pobreza por ingresos aparecen en "
        f"{_format_name_list(worst_pobreza)}.",
        "- Los menores niveles de IPP por habitante aparecen en "
        f"{_format_name_list(worst_ipp)}.",
        "- El cruce descriptivo muestra que "
        f"{_format_name_list(cross_pobreza_areas)} combinan rezago en pobreza y areas verdes, "
        f"mientras que {_format_name_list(cross_pobreza_ipp)} combinan rezago en pobreza e IPP por habitante.",
        "- Las comunas con rezago critico en al menos dos dimensiones son "
        f"{_format_name_list(rezago_multiple)}.",
        "",
        "## Graficos generados",
    ]

    for figure_path in figure_paths:
        lines.append(f"- `{_relpath(figure_path)}`")

    lines.extend(
        [
            "- `pobreza_vs_areas_verdes_scatter.png` se regenero con escala logaritmica en el eje X y una advertencia explicita sobre QUILICURA.",
        ]
    )

    lines.extend(
        [
            "",
            "## Outputs tabulares",
            f"- `{_relpath(TABLAS_HALLAZGOS_FASE9_CSV_PATH)}`",
            f"- `{_relpath(RANKING_AREAS_VERDES_CSV_PATH)}`",
            f"- `{_relpath(RANKING_POBREZA_CSV_PATH)}`",
            f"- `{_relpath(RANKING_IPP_CSV_PATH)}`",
            f"- `{_relpath(INDICE_REZAGO_TERRITORIAL_CSV_PATH)}`",
        ]
    )
    return "\n".join(lines) + "\n"


def export_analysis_markdown(
    markdown: str,
    path: Path = ANALISIS_EXPLORATORIO_MD_PATH,
) -> None:
    path.write_text(markdown, encoding="utf-8")


def run_phase_9_analysis(
    final_df: pd.DataFrame | None = None,
    dataset_path: Path = FINAL_DATASET_PATH,
    sqlite_path: Path = SQLITE_PATH,
) -> dict[str, object]:
    ensure_directories()
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    source_df = final_df.copy() if final_df is not None else load_final_dataset(dataset_path)
    canonical_df = prepare_final_dataset(source_df)

    phase_7_result = run_phase_7_validation(
        final_df=canonical_df,
        dataset_path=dataset_path,
    )
    if not phase_7_result["validation_result"].is_valid:
        raise ValueError("El dataset final no esta validado para analisis. Fase 9 se detiene.")

    sqlite_df = load_sqlite_analysis_view(sqlite_path)
    consistency_result = validate_csv_sqlite_consistency(canonical_df, sqlite_df)
    if not consistency_result["is_consistent"]:
        raise ValueError(
            "CSV y SQLite no son consistentes para Fase 9. "
            f"csv_only={list(consistency_result['csv_only_codes'])}; "
            f"sqlite_only={list(consistency_result['sqlite_only_codes'])}; "
            f"name_mismatches={consistency_result['name_mismatches']}; "
            f"numeric_mismatches={consistency_result['numeric_mismatch_counts']}"
        )

    enriched_df = enrich_analysis_dataset(canonical_df)
    rankings = build_rankings(enriched_df)
    cross_tables = build_cross_tables(enriched_df)
    full_exports = build_full_export_tables(enriched_df)

    full_exports["ranking_areas_verdes"].to_csv(
        RANKING_AREAS_VERDES_CSV_PATH,
        index=False,
        encoding="utf-8",
    )
    full_exports["ranking_pobreza"].to_csv(
        RANKING_POBREZA_CSV_PATH,
        index=False,
        encoding="utf-8",
    )
    full_exports["ranking_ipp"].to_csv(
        RANKING_IPP_CSV_PATH,
        index=False,
        encoding="utf-8",
    )
    full_exports["indice_rezago_territorial"].to_csv(
        INDICE_REZAGO_TERRITORIAL_CSV_PATH,
        index=False,
        encoding="utf-8",
    )

    hallazgos_df = build_hallazgos_table(rankings, cross_tables)
    figure_paths = create_figures(enriched_df, full_exports)
    markdown = build_analysis_markdown(
        consistency_result=consistency_result,
        rankings=rankings,
        cross_tables=cross_tables,
        figure_paths=figure_paths,
    )
    export_analysis_markdown(markdown)

    return {
        "canonical_dataset": canonical_df,
        "sqlite_dataset": sqlite_df,
        "consistency_result": consistency_result,
        "enriched_dataset": enriched_df,
        "rankings": rankings,
        "cross_tables": cross_tables,
        "hallazgos_df": hallazgos_df,
        "full_exports": full_exports,
        "figure_paths": figure_paths,
        "analysis_markdown": markdown,
        "analysis_markdown_path": ANALISIS_EXPLORATORIO_MD_PATH,
        "hallazgos_csv_path": TABLAS_HALLAZGOS_FASE9_CSV_PATH,
        "ranking_paths": (
            RANKING_AREAS_VERDES_CSV_PATH,
            RANKING_POBREZA_CSV_PATH,
            RANKING_IPP_CSV_PATH,
            INDICE_REZAGO_TERRITORIAL_CSV_PATH,
        ),
        "phase_7_result": phase_7_result,
    }


if __name__ == "__main__":
    result = run_phase_9_analysis()
    print(f"Analisis: {_relpath(result['analysis_markdown_path'])}")
    print(f"Tablas: {_relpath(result['hallazgos_csv_path'])}")
