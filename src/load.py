from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from src.config import (
    BASE_DIR,
    DIM_COMUNA_BASE_PATH,
    EXPECTED_DIM_COMUNA_ROWS,
    FINAL_DATASET_PATH,
    METADATA_PATH,
    METADATA_REQUIRED_COLUMNS,
    RAW_SOURCES,
    REPORTE_CARGA_SQLITE_MD_PATH,
    REPORTE_CONSULTAS_SQLITE_CSV_PATH,
    SQLITE_PATH,
    ensure_directories,
)
from src.validate import load_final_dataset, run_phase_7_validation

DIM_COMUNA_COLUMNS = (
    "codigo_comuna",
    "nombre_comuna",
    "provincia",
    "region",
    "fuente_referencia",
)

FACT_TABLE_COLUMNS = (
    "codigo_comuna",
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

INTEGER_FACT_COLUMNS = (
    "poblacion",
    "anio_poblacion",
    "anio_pobreza",
    "areas_verdes_m2",
    "anio_areas_verdes",
    "ipp_miles_pesos",
    "anio_ingresos",
)

FLOAT_FACT_COLUMNS = (
    "pobreza_ingresos_pct",
    "areas_verdes_m2_hab",
    "ipp_pesos_hab",
)


def _relpath(path: Path) -> str:
    return path.relative_to(BASE_DIR).as_posix()


def _clean_string_series(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().replace("", pd.NA)


def _format_codigo_comuna(series: pd.Series) -> pd.Series:
    cleaned = _clean_string_series(series)
    numeric = pd.to_numeric(cleaned, errors="coerce").astype("Int64")
    return numeric.map(
        lambda value: f"{int(value):05d}" if pd.notna(value) else pd.NA
    ).astype("string")


def prepare_dim_comuna(dataframe: pd.DataFrame) -> pd.DataFrame:
    actual_columns = tuple(map(str, dataframe.columns))
    missing_columns = [
        column for column in DIM_COMUNA_COLUMNS if column not in actual_columns
    ]
    if missing_columns:
        raise ValueError(
            "La dimension comunal no contiene todas las columnas requeridas para Fase 8. "
            f"Faltantes={missing_columns}; observado={actual_columns}."
        )

    dataframe = dataframe[list(DIM_COMUNA_COLUMNS)].copy()
    dataframe["codigo_comuna"] = _format_codigo_comuna(dataframe["codigo_comuna"])
    for column in ("nombre_comuna", "provincia", "region", "fuente_referencia"):
        dataframe[column] = _clean_string_series(dataframe[column])

    if len(dataframe) != EXPECTED_DIM_COMUNA_ROWS:
        raise ValueError(
            "La dimension comunal debe contener 32 filas y hoy contiene "
            f"{len(dataframe)}."
        )
    if int(dataframe["codigo_comuna"].isna().sum()) != 0:
        raise ValueError("La dimension comunal tiene `codigo_comuna` nulo.")
    if int(dataframe["codigo_comuna"].duplicated().sum()) != 0:
        raise ValueError("La dimension comunal tiene duplicados por `codigo_comuna`.")

    return dataframe


def load_dim_comuna(path: Path = DIM_COMUNA_BASE_PATH) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"No existe la dimension comunal base: {_relpath(path)}")

    dataframe = pd.read_csv(path, dtype={"codigo_comuna": "string"})
    return prepare_dim_comuna(dataframe)


def load_metadata_fuentes(
    path: Path = METADATA_PATH,
) -> tuple[pd.DataFrame, dict[str, object]]:
    empty = pd.DataFrame(columns=METADATA_REQUIRED_COLUMNS)
    if not path.exists():
        return empty, {"loaded": False, "row_count": 0, "reason": "archivo ausente"}

    dataframe = pd.read_csv(path, dtype="string")
    dataframe = prepare_metadata_table(dataframe)
    expected_ids = tuple(RAW_SOURCES.keys())
    observed_ids = tuple(dataframe["id_fuente"].astype(str))
    if observed_ids != expected_ids:
        raise ValueError(
            "metadata_fuentes.csv debe documentar exactamente las fuentes A-D en orden. "
            f"Observado={observed_ids}."
        )

    return dataframe, {"loaded": True, "row_count": len(dataframe), "reason": "ok"}


def prepare_metadata_table(dataframe: pd.DataFrame) -> pd.DataFrame:
    actual_columns = tuple(map(str, dataframe.columns))
    missing_columns = [
        column for column in METADATA_REQUIRED_COLUMNS if column not in actual_columns
    ]
    if missing_columns:
        raise ValueError(
            "La tabla metadata_fuentes no contiene todas las columnas requeridas. "
            f"Faltantes={missing_columns}; observado={actual_columns}."
        )

    dataframe = dataframe[list(METADATA_REQUIRED_COLUMNS)].copy()
    for column in dataframe.columns:
        dataframe[column] = _clean_string_series(dataframe[column])

    dataframe["anio_referencia"] = pd.to_numeric(
        dataframe["anio_referencia"], errors="coerce"
    ).astype("Int64")
    dataframe["skiprows"] = pd.to_numeric(
        dataframe["skiprows"], errors="coerce"
    ).astype("Int64")

    if int(dataframe["id_fuente"].isna().sum()) != 0:
        raise ValueError("La tabla metadata_fuentes tiene `id_fuente` nulo.")
    if int(dataframe["id_fuente"].duplicated().sum()) != 0:
        raise ValueError("La tabla metadata_fuentes tiene duplicados por `id_fuente`.")

    return dataframe


def prepare_final_dataset(final_df: pd.DataFrame) -> pd.DataFrame:
    dataframe = final_df.copy()
    actual_columns = tuple(map(str, dataframe.columns))
    if actual_columns != FINAL_DATASET_COLUMNS:
        raise ValueError(
            "El dataset final no coincide con el esquema esperado para Fase 8. "
            f"Esperado={FINAL_DATASET_COLUMNS}; observado={actual_columns}."
        )

    dataframe["codigo_comuna"] = _format_codigo_comuna(dataframe["codigo_comuna"])
    dataframe["nombre_comuna"] = _clean_string_series(dataframe["nombre_comuna"])

    for column in INTEGER_FACT_COLUMNS:
        dataframe[column] = pd.to_numeric(dataframe[column], errors="coerce").astype("Int64")
    for column in FLOAT_FACT_COLUMNS:
        dataframe[column] = pd.to_numeric(dataframe[column], errors="coerce").astype("Float64")

    if len(dataframe) != EXPECTED_DIM_COMUNA_ROWS:
        raise ValueError(
            "El dataset final debe contener 32 filas para cargar a SQLite y hoy contiene "
            f"{len(dataframe)}."
        )
    if int(dataframe["codigo_comuna"].isna().sum()) != 0:
        raise ValueError("El dataset final tiene `codigo_comuna` nulo.")
    if int(dataframe["codigo_comuna"].duplicated().sum()) != 0:
        raise ValueError("El dataset final tiene duplicados por `codigo_comuna`.")

    return dataframe[list(FINAL_DATASET_COLUMNS)]


def prepare_fact_table(dataframe: pd.DataFrame) -> pd.DataFrame:
    actual_columns = tuple(map(str, dataframe.columns))
    missing_columns = [column for column in FACT_TABLE_COLUMNS if column not in actual_columns]
    if missing_columns:
        raise ValueError(
            "La tabla de hechos no contiene todas las columnas requeridas para Fase 8. "
            f"Faltantes={missing_columns}; observado={actual_columns}."
        )

    dataframe = dataframe[list(FACT_TABLE_COLUMNS)].copy()
    dataframe["codigo_comuna"] = _format_codigo_comuna(dataframe["codigo_comuna"])

    for column in INTEGER_FACT_COLUMNS:
        dataframe[column] = pd.to_numeric(dataframe[column], errors="coerce").astype("Int64")
    for column in FLOAT_FACT_COLUMNS:
        dataframe[column] = pd.to_numeric(dataframe[column], errors="coerce").astype("Float64")

    if int(dataframe["codigo_comuna"].isna().sum()) != 0:
        raise ValueError("La tabla de hechos tiene `codigo_comuna` nulo.")
    if int(dataframe["codigo_comuna"].duplicated().sum()) != 0:
        raise ValueError("La tabla de hechos tiene duplicados por `codigo_comuna`.")

    return dataframe


def _to_python_value(value: object) -> object:
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def _records_from_dataframe(
    dataframe: pd.DataFrame,
    columns: tuple[str, ...],
) -> list[tuple[object, ...]]:
    records: list[tuple[object, ...]] = []
    for _, row in dataframe.loc[:, columns].iterrows():
        records.append(tuple(_to_python_value(row[column]) for column in columns))
    return records


def _sorted_records(
    dataframe: pd.DataFrame,
    columns: tuple[str, ...],
    sort_by: tuple[str, ...],
) -> list[tuple[object, ...]]:
    ordered = dataframe.loc[:, list(columns)].sort_values(
        list(sort_by),
        kind="stable",
        na_position="last",
    )
    ordered = ordered.reset_index(drop=True)
    return _records_from_dataframe(ordered, columns)


def _sqlite_has_expected_content(
    connection: sqlite3.Connection,
    dim_comuna_df: pd.DataFrame,
    fact_df: pd.DataFrame,
    metadata_df: pd.DataFrame,
) -> bool:
    expected_tables = ("dim_comuna", "fact_desigualdad_comunal", "metadata_fuentes")
    if _fetch_table_names(connection) != expected_tables:
        return False
    if str(connection.execute("PRAGMA quick_check").fetchone()[0]) != "ok":
        return False

    try:
        current_dim_df = prepare_dim_comuna(
            pd.read_sql_query(
                """
                SELECT codigo_comuna, nombre_comuna, provincia, region, fuente_referencia
                FROM dim_comuna
                """,
                connection,
            )
        )
        current_fact_df = prepare_fact_table(
            pd.read_sql_query(
                """
                SELECT codigo_comuna, poblacion, anio_poblacion, pobreza_ingresos_pct,
                       anio_pobreza, areas_verdes_m2, anio_areas_verdes, ipp_miles_pesos,
                       anio_ingresos, areas_verdes_m2_hab, ipp_pesos_hab
                FROM fact_desigualdad_comunal
                """,
                connection,
            )
        )
        current_metadata_df = prepare_metadata_table(
            pd.read_sql_query(
                """
                SELECT id_fuente, nombre_fuente, institucion, url, fecha_descarga, formato,
                       anio_referencia, variable_principal, archivo_origen, archivo_logico,
                       hoja, skiprows, observaciones
                FROM metadata_fuentes
                """,
                connection,
            )
        )
    except (ValueError, pd.errors.DatabaseError, sqlite3.Error):
        return False

    return (
        _sorted_records(current_dim_df, DIM_COMUNA_COLUMNS, ("codigo_comuna",))
        == _sorted_records(dim_comuna_df, DIM_COMUNA_COLUMNS, ("codigo_comuna",))
        and _sorted_records(current_fact_df, FACT_TABLE_COLUMNS, ("codigo_comuna",))
        == _sorted_records(fact_df, FACT_TABLE_COLUMNS, ("codigo_comuna",))
        and _sorted_records(current_metadata_df, METADATA_REQUIRED_COLUMNS, ("id_fuente",))
        == _sorted_records(metadata_df, METADATA_REQUIRED_COLUMNS, ("id_fuente",))
    )


def _reset_sqlite_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        PRAGMA foreign_keys = OFF;

        DROP TABLE IF EXISTS fact_desigualdad_comunal;
        DROP TABLE IF EXISTS dim_comuna;
        DROP TABLE IF EXISTS metadata_fuentes;

        CREATE TABLE dim_comuna (
            codigo_comuna TEXT PRIMARY KEY,
            nombre_comuna TEXT NOT NULL,
            provincia TEXT NOT NULL,
            region TEXT NOT NULL,
            fuente_referencia TEXT NOT NULL
        );

        CREATE TABLE fact_desigualdad_comunal (
            codigo_comuna TEXT PRIMARY KEY,
            poblacion INTEGER,
            anio_poblacion INTEGER,
            pobreza_ingresos_pct REAL,
            anio_pobreza INTEGER,
            areas_verdes_m2 INTEGER,
            anio_areas_verdes INTEGER,
            ipp_miles_pesos INTEGER,
            anio_ingresos INTEGER,
            areas_verdes_m2_hab REAL,
            ipp_pesos_hab REAL,
            FOREIGN KEY (codigo_comuna) REFERENCES dim_comuna (codigo_comuna)
        );

        CREATE TABLE metadata_fuentes (
            id_fuente TEXT PRIMARY KEY,
            nombre_fuente TEXT NOT NULL,
            institucion TEXT NOT NULL,
            url TEXT NOT NULL,
            fecha_descarga TEXT NOT NULL,
            formato TEXT NOT NULL,
            anio_referencia INTEGER,
            variable_principal TEXT NOT NULL,
            archivo_origen TEXT NOT NULL,
            archivo_logico TEXT NOT NULL,
            hoja TEXT NOT NULL,
            skiprows INTEGER,
            observaciones TEXT
        );

        PRAGMA foreign_keys = ON;
        """
    )


def _load_tables_into_sqlite(
    connection: sqlite3.Connection,
    dim_comuna_df: pd.DataFrame,
    fact_df: pd.DataFrame,
    metadata_df: pd.DataFrame,
) -> None:
    fact_name_check = fact_df[["codigo_comuna", "nombre_comuna"]].merge(
        dim_comuna_df[["codigo_comuna", "nombre_comuna"]],
        on="codigo_comuna",
        how="left",
        suffixes=("_fact", "_dim"),
    )
    mismatched_names = fact_name_check[
        fact_name_check["nombre_comuna_fact"] != fact_name_check["nombre_comuna_dim"]
    ]
    if not mismatched_names.empty:
        raise ValueError(
            "El dataset final no coincide con la dimension comunal en `nombre_comuna`."
        )

    dim_records = _records_from_dataframe(dim_comuna_df, DIM_COMUNA_COLUMNS)
    fact_records = _records_from_dataframe(fact_df, FACT_TABLE_COLUMNS)
    metadata_records = _records_from_dataframe(metadata_df, METADATA_REQUIRED_COLUMNS)

    connection.executemany(
        """
        INSERT INTO dim_comuna (
            codigo_comuna,
            nombre_comuna,
            provincia,
            region,
            fuente_referencia
        ) VALUES (?, ?, ?, ?, ?)
        """,
        dim_records,
    )
    connection.executemany(
        """
        INSERT INTO fact_desigualdad_comunal (
            codigo_comuna,
            poblacion,
            anio_poblacion,
            pobreza_ingresos_pct,
            anio_pobreza,
            areas_verdes_m2,
            anio_areas_verdes,
            ipp_miles_pesos,
            anio_ingresos,
            areas_verdes_m2_hab,
            ipp_pesos_hab
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        fact_records,
    )
    if metadata_records:
        connection.executemany(
            """
            INSERT INTO metadata_fuentes (
                id_fuente,
                nombre_fuente,
                institucion,
                url,
                fecha_descarga,
                formato,
                anio_referencia,
                variable_principal,
                archivo_origen,
                archivo_logico,
                hoja,
                skiprows,
                observaciones
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            metadata_records,
        )


def _fetch_table_names(connection: sqlite3.Connection) -> tuple[str, ...]:
    cursor = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
    )
    return tuple(row[0] for row in cursor.fetchall())


def _fetch_row_counts(connection: sqlite3.Connection) -> dict[str, int]:
    row_counts: dict[str, int] = {}
    for table_name in ("dim_comuna", "fact_desigualdad_comunal", "metadata_fuentes"):
        row_counts[table_name] = int(
            connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        )
    return row_counts


def _fetch_duplicate_count(
    connection: sqlite3.Connection,
    table_name: str,
) -> int:
    query = f"""
        SELECT COUNT(*)
        FROM (
            SELECT codigo_comuna
            FROM {table_name}
            GROUP BY codigo_comuna
            HAVING COUNT(*) > 1
        )
    """
    return int(connection.execute(query).fetchone()[0])


def _fetch_coverage(connection: sqlite3.Connection) -> dict[str, int]:
    fact_without_dim = int(
        connection.execute(
            """
            SELECT COUNT(*)
            FROM fact_desigualdad_comunal AS fact
            LEFT JOIN dim_comuna AS dim
                ON dim.codigo_comuna = fact.codigo_comuna
            WHERE dim.codigo_comuna IS NULL
            """
        ).fetchone()[0]
    )
    dim_without_fact = int(
        connection.execute(
            """
            SELECT COUNT(*)
            FROM dim_comuna AS dim
            LEFT JOIN fact_desigualdad_comunal AS fact
                ON fact.codigo_comuna = dim.codigo_comuna
            WHERE fact.codigo_comuna IS NULL
            """
        ).fetchone()[0]
    )
    return {
        "fact_without_dim": fact_without_dim,
        "dim_without_fact": dim_without_fact,
    }


def _fetch_schema_info(
    connection: sqlite3.Connection,
    table_names: tuple[str, ...],
) -> dict[str, list[dict[str, object]]]:
    schema_info: dict[str, list[dict[str, object]]] = {}
    for table_name in table_names:
        rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
        schema_info[table_name] = [
            {
                "cid": row[0],
                "name": row[1],
                "type": row[2],
                "notnull": row[3],
                "default": row[4],
                "pk": row[5],
            }
            for row in rows
        ]
    return schema_info


def _fetch_query_results(
    connection: sqlite3.Connection,
) -> dict[str, list[dict[str, object]]]:
    query_results: dict[str, list[dict[str, object]]] = {}

    row_counts = connection.execute(
        """
        SELECT 'dim_comuna' AS tabla, COUNT(*) AS filas FROM dim_comuna
        UNION ALL
        SELECT 'fact_desigualdad_comunal' AS tabla, COUNT(*) AS filas FROM fact_desigualdad_comunal
        UNION ALL
        SELECT 'metadata_fuentes' AS tabla, COUNT(*) AS filas FROM metadata_fuentes
        ORDER BY tabla
        """
    ).fetchall()
    query_results["conteo_filas_por_tabla"] = [
        {"tabla": row[0], "filas": int(row[1])} for row in row_counts
    ]

    menor_areas_verdes = connection.execute(
        """
        SELECT fact.codigo_comuna, dim.nombre_comuna, fact.areas_verdes_m2_hab
        FROM fact_desigualdad_comunal AS fact
        INNER JOIN dim_comuna AS dim
            ON dim.codigo_comuna = fact.codigo_comuna
        WHERE fact.areas_verdes_m2_hab IS NOT NULL
        ORDER BY fact.areas_verdes_m2_hab ASC, fact.codigo_comuna ASC
        LIMIT 5
        """
    ).fetchall()
    query_results["top_5_menor_areas_verdes_m2_hab"] = [
        {
            "codigo_comuna": row[0],
            "nombre_comuna": row[1],
            "areas_verdes_m2_hab": float(row[2]),
        }
        for row in menor_areas_verdes
    ]

    mayor_pobreza = connection.execute(
        """
        SELECT fact.codigo_comuna, dim.nombre_comuna, fact.pobreza_ingresos_pct
        FROM fact_desigualdad_comunal AS fact
        INNER JOIN dim_comuna AS dim
            ON dim.codigo_comuna = fact.codigo_comuna
        WHERE fact.pobreza_ingresos_pct IS NOT NULL
        ORDER BY fact.pobreza_ingresos_pct DESC, fact.codigo_comuna ASC
        LIMIT 5
        """
    ).fetchall()
    query_results["top_5_mayor_pobreza_ingresos_pct"] = [
        {
            "codigo_comuna": row[0],
            "nombre_comuna": row[1],
            "pobreza_ingresos_pct": float(row[2]),
        }
        for row in mayor_pobreza
    ]

    menor_ipp = connection.execute(
        """
        SELECT fact.codigo_comuna, dim.nombre_comuna, fact.ipp_pesos_hab
        FROM fact_desigualdad_comunal AS fact
        INNER JOIN dim_comuna AS dim
            ON dim.codigo_comuna = fact.codigo_comuna
        WHERE fact.ipp_pesos_hab IS NOT NULL
        ORDER BY fact.ipp_pesos_hab ASC, fact.codigo_comuna ASC
        LIMIT 5
        """
    ).fetchall()
    query_results["top_5_menor_ipp_pesos_hab"] = [
        {
            "codigo_comuna": row[0],
            "nombre_comuna": row[1],
            "ipp_pesos_hab": float(row[2]),
        }
        for row in menor_ipp
    ]

    duplicates = connection.execute(
        """
        SELECT codigo_comuna, COUNT(*) AS repeticiones
        FROM fact_desigualdad_comunal
        GROUP BY codigo_comuna
        HAVING COUNT(*) > 1
        ORDER BY codigo_comuna
        """
    ).fetchall()
    query_results["unicidad_codigo_fact"] = [
        {"codigo_comuna": row[0], "repeticiones": int(row[1])}
        for row in duplicates
    ]

    return query_results


def export_query_results_csv(
    query_results: dict[str, list[dict[str, object]]],
    duplicate_counts: dict[str, int],
    coverage: dict[str, int],
    path: Path = REPORTE_CONSULTAS_SQLITE_CSV_PATH,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    for row in query_results["conteo_filas_por_tabla"]:
        rows.append(
            {
                "consulta": "conteo_filas_por_tabla",
                "orden": None,
                "tabla": row["tabla"],
                "codigo_comuna": None,
                "nombre_comuna": None,
                "valor": row["filas"],
                "detalle": "conteo de filas",
            }
        )

    for order, row in enumerate(query_results["top_5_menor_areas_verdes_m2_hab"], start=1):
        rows.append(
            {
                "consulta": "top_5_menor_areas_verdes_m2_hab",
                "orden": order,
                "tabla": "fact_desigualdad_comunal",
                "codigo_comuna": row["codigo_comuna"],
                "nombre_comuna": row["nombre_comuna"],
                "valor": row["areas_verdes_m2_hab"],
                "detalle": "areas_verdes_m2_hab",
            }
        )

    for order, row in enumerate(query_results["top_5_mayor_pobreza_ingresos_pct"], start=1):
        rows.append(
            {
                "consulta": "top_5_mayor_pobreza_ingresos_pct",
                "orden": order,
                "tabla": "fact_desigualdad_comunal",
                "codigo_comuna": row["codigo_comuna"],
                "nombre_comuna": row["nombre_comuna"],
                "valor": row["pobreza_ingresos_pct"],
                "detalle": "pobreza_ingresos_pct",
            }
        )

    for order, row in enumerate(query_results["top_5_menor_ipp_pesos_hab"], start=1):
        rows.append(
            {
                "consulta": "top_5_menor_ipp_pesos_hab",
                "orden": order,
                "tabla": "fact_desigualdad_comunal",
                "codigo_comuna": row["codigo_comuna"],
                "nombre_comuna": row["nombre_comuna"],
                "valor": row["ipp_pesos_hab"],
                "detalle": "ipp_pesos_hab",
            }
        )

    rows.append(
        {
            "consulta": "unicidad_codigo_fact",
            "orden": 1,
            "tabla": "fact_desigualdad_comunal",
            "codigo_comuna": None,
            "nombre_comuna": None,
            "valor": duplicate_counts["fact_desigualdad_comunal"],
            "detalle": "cantidad de codigos duplicados detectados en fact",
        }
    )
    rows.append(
        {
            "consulta": "cobertura_fact_vs_dim",
            "orden": 1,
            "tabla": "fact_desigualdad_comunal",
            "codigo_comuna": None,
            "nombre_comuna": None,
            "valor": coverage["fact_without_dim"],
            "detalle": "codigos presentes en fact y ausentes en dim",
        }
    )
    rows.append(
        {
            "consulta": "cobertura_dim_vs_fact",
            "orden": 1,
            "tabla": "dim_comuna",
            "codigo_comuna": None,
            "nombre_comuna": None,
            "valor": coverage["dim_without_fact"],
            "detalle": "codigos presentes en dim y ausentes en fact",
        }
    )

    dataframe = pd.DataFrame(rows)
    dataframe.to_csv(path, index=False, encoding="utf-8")
    return dataframe


def build_sqlite_report_markdown(
    dataset_path: Path,
    sqlite_path: Path,
    table_names: tuple[str, ...],
    row_counts: dict[str, int],
    validation_checks: list[dict[str, object]],
    schema_info: dict[str, list[dict[str, object]]],
    query_results: dict[str, list[dict[str, object]]],
    metadata_info: dict[str, object],
) -> str:
    lines = [
        "# Reporte de carga SQLite",
        "",
        "## Insumo de carga",
        f"- Dataset final utilizado: `{_relpath(dataset_path)}`",
        "- Validacion previa obligatoria: Fase 7 ejecutada y dataset marcado como apto para SQLite.",
        f"- Base SQLite generada: `{_relpath(sqlite_path)}`",
        f"- Tablas creadas: {', '.join(table_names)}",
        "",
        "## Validacion formal",
    ]

    for check in validation_checks:
        status = "OK" if bool(check["is_valid"]) else "ERROR"
        lines.append(
            f"- [{status}] {check['description']} "
            f"(observado: {check['observed']}; esperado: {check['expected']})."
        )
        lines.append(f"  {check['detail']}")

    lines.extend(
        [
            "",
            "## Conteo de filas por tabla",
        ]
    )
    for table_name, row_count in row_counts.items():
        lines.append(f"- `{table_name}`: {row_count}")

    lines.extend(
        [
            "",
            "## Metadata de fuentes",
            f"- Metadata cargada: {'si' if metadata_info['loaded'] else 'no'}",
            f"- Filas en metadata_fuentes: {metadata_info['row_count']}",
            f"- Estado metadata: {metadata_info['reason']}",
            "",
            "## Consultas obligatorias",
            "### Top 5 comunas con menor `areas_verdes_m2_hab`",
        ]
    )
    for order, row in enumerate(query_results["top_5_menor_areas_verdes_m2_hab"], start=1):
        lines.append(
            f"- {order}. {row['nombre_comuna']} ({row['codigo_comuna']}): "
            f"{row['areas_verdes_m2_hab']:.6f}"
        )

    lines.append("")
    lines.append("### Top 5 comunas con mayor `pobreza_ingresos_pct`")
    for order, row in enumerate(query_results["top_5_mayor_pobreza_ingresos_pct"], start=1):
        lines.append(
            f"- {order}. {row['nombre_comuna']} ({row['codigo_comuna']}): "
            f"{row['pobreza_ingresos_pct']:.4f}"
        )

    lines.append("")
    lines.append("### Top 5 comunas con menor `ipp_pesos_hab`")
    for order, row in enumerate(query_results["top_5_menor_ipp_pesos_hab"], start=1):
        lines.append(
            f"- {order}. {row['nombre_comuna']} ({row['codigo_comuna']}): "
            f"{row['ipp_pesos_hab']:.6f}"
        )

    lines.extend(
        [
            "",
            "## Estructura de tablas",
        ]
    )
    for table_name in table_names:
        lines.append(f"### {table_name}")
        for column in schema_info[table_name]:
            lines.append(
                f"- `{column['name']}` {column['type']} "
                f"(pk={column['pk']}, notnull={column['notnull']}, default={column['default']})"
            )
        lines.append("")

    lines.extend(
        [
            "## Cierre",
            "- La base queda consultable desde SQLite y preserva `codigo_comuna` como llave central.",
            "- La combinacion `dim_comuna` + `fact_desigualdad_comunal` reproduce el dataset final validado.",
            "- `metadata_fuentes` documenta el contrato operativo de las fuentes utilizadas en el ETL.",
        ]
    )
    return "\n".join(lines) + "\n"


def export_sqlite_report_markdown(
    markdown: str,
    path: Path = REPORTE_CARGA_SQLITE_MD_PATH,
) -> None:
    path.write_text(markdown, encoding="utf-8")


def run_phase_8_load(
    final_df: pd.DataFrame | None = None,
    dim_base: pd.DataFrame | None = None,
    dataset_path: Path = FINAL_DATASET_PATH,
    sqlite_path: Path = SQLITE_PATH,
) -> dict[str, object]:
    ensure_directories()

    source_dim_df = dim_base.copy() if dim_base is not None else load_dim_comuna()
    dim_comuna_df = prepare_dim_comuna(source_dim_df)
    source_final_df = final_df.copy() if final_df is not None else load_final_dataset(dataset_path)
    final_dataset_df = prepare_final_dataset(source_final_df)

    phase_7_result = run_phase_7_validation(
        final_df=final_dataset_df,
        dim_base=dim_comuna_df.copy(),
        dataset_path=dataset_path,
    )
    if not phase_7_result["validation_result"].is_valid:
        raise ValueError(
            "El dataset final no es apto para SQLite segun Fase 7. La carga se detiene."
        )

    metadata_df, metadata_info = load_metadata_fuentes()
    fact_table_df = prepare_fact_table(final_dataset_df)

    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    sqlite_exists = sqlite_path.exists()
    with sqlite3.connect(sqlite_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        sqlite_reused = sqlite_exists and _sqlite_has_expected_content(
            connection=connection,
            dim_comuna_df=dim_comuna_df,
            fact_df=fact_table_df,
            metadata_df=metadata_df,
        )

        # Evita reserializar SQLite cuando el contenido tabular ya coincide.
        if not sqlite_reused:
            _reset_sqlite_schema(connection)
            _load_tables_into_sqlite(
                connection=connection,
                dim_comuna_df=dim_comuna_df,
                fact_df=final_dataset_df,
                metadata_df=metadata_df,
            )
            connection.commit()

        quick_check = str(connection.execute("PRAGMA quick_check").fetchone()[0])
        table_names = _fetch_table_names(connection)
        row_counts = _fetch_row_counts(connection)
        duplicate_counts = {
            "dim_comuna": _fetch_duplicate_count(connection, "dim_comuna"),
            "fact_desigualdad_comunal": _fetch_duplicate_count(
                connection, "fact_desigualdad_comunal"
            ),
        }
        coverage = _fetch_coverage(connection)
        schema_info = _fetch_schema_info(connection, table_names)
        query_results = _fetch_query_results(connection)

    expected_tables = ("dim_comuna", "fact_desigualdad_comunal", "metadata_fuentes")
    validation_checks = [
        {
            "check_id": "archivo_sqlite_existe",
            "description": "El archivo SQLite existe en la ruta esperada.",
            "is_valid": sqlite_path.exists(),
            "observed": _relpath(sqlite_path) if sqlite_path.exists() else "ausente",
            "expected": _relpath(sqlite_path),
            "detail": "Ruta estable del entregable final de Fase 8.",
        },
        {
            "check_id": "apertura_sqlite",
            "description": "La base abre correctamente y supera `PRAGMA quick_check`.",
            "is_valid": quick_check == "ok",
            "observed": quick_check,
            "expected": "ok",
            "detail": "Chequeo rapido de integridad del archivo SQLite.",
        },
        {
            "check_id": "tablas_esperadas",
            "description": "Existen las tablas esperadas en la base.",
            "is_valid": tuple(table_names) == expected_tables,
            "observed": ", ".join(table_names),
            "expected": ", ".join(expected_tables),
            "detail": "Modelo fisico minimo requerido para la entrega.",
        },
        {
            "check_id": "dim_comuna_32",
            "description": "`dim_comuna` contiene 32 filas.",
            "is_valid": row_counts["dim_comuna"] == EXPECTED_DIM_COMUNA_ROWS,
            "observed": row_counts["dim_comuna"],
            "expected": EXPECTED_DIM_COMUNA_ROWS,
            "detail": "Cobertura completa de comunas de la Provincia de Santiago.",
        },
        {
            "check_id": "fact_32",
            "description": "`fact_desigualdad_comunal` contiene 32 filas.",
            "is_valid": row_counts["fact_desigualdad_comunal"] == EXPECTED_DIM_COMUNA_ROWS,
            "observed": row_counts["fact_desigualdad_comunal"],
            "expected": EXPECTED_DIM_COMUNA_ROWS,
            "detail": "Una fila por comuna en la tabla de hechos.",
        },
        {
            "check_id": "metadata_cargada",
            "description": "`metadata_fuentes` se cargo segun el archivo fuente disponible.",
            "is_valid": (
                not metadata_info["loaded"]
                or row_counts["metadata_fuentes"] == int(metadata_info["row_count"])
            ),
            "observed": row_counts["metadata_fuentes"],
            "expected": metadata_info["row_count"],
            "detail": (
                "La tabla queda poblada con el contrato operativo de lectura."
                if metadata_info["loaded"]
                else "No aplica carga de metadata porque el archivo no existe."
            ),
        },
        {
            "check_id": "dim_sin_duplicados",
            "description": "`dim_comuna` no tiene duplicados por `codigo_comuna`.",
            "is_valid": duplicate_counts["dim_comuna"] == 0,
            "observed": duplicate_counts["dim_comuna"],
            "expected": 0,
            "detail": "Unicidad de la llave en la dimension.",
        },
        {
            "check_id": "fact_sin_duplicados",
            "description": "`fact_desigualdad_comunal` no tiene duplicados por `codigo_comuna`.",
            "is_valid": duplicate_counts["fact_desigualdad_comunal"] == 0,
            "observed": duplicate_counts["fact_desigualdad_comunal"],
            "expected": 0,
            "detail": "Unicidad de la llave en la tabla de hechos.",
        },
        {
            "check_id": "cobertura_fact_dim",
            "description": "La cobertura entre `fact_desigualdad_comunal` y `dim_comuna` coincide exactamente.",
            "is_valid": coverage["fact_without_dim"] == 0 and coverage["dim_without_fact"] == 0,
            "observed": (
                f"fact_sin_dim={coverage['fact_without_dim']}; "
                f"dim_sin_fact={coverage['dim_without_fact']}"
            ),
            "expected": "fact_sin_dim=0; dim_sin_fact=0",
            "detail": "No hay codigos huerfanos entre ambas tablas.",
        },
        {
            "check_id": "consultas_reproducibles",
            "description": "Las consultas obligatorias retornan resultados reproducibles.",
            "is_valid": (
                len(query_results["conteo_filas_por_tabla"]) == 3
                and len(query_results["top_5_menor_areas_verdes_m2_hab"]) == 5
                and len(query_results["top_5_mayor_pobreza_ingresos_pct"]) == 5
                and len(query_results["top_5_menor_ipp_pesos_hab"]) == 5
            ),
            "observed": (
                f"conteos={len(query_results['conteo_filas_por_tabla'])}; "
                f"areas={len(query_results['top_5_menor_areas_verdes_m2_hab'])}; "
                f"pobreza={len(query_results['top_5_mayor_pobreza_ingresos_pct'])}; "
                f"ipp={len(query_results['top_5_menor_ipp_pesos_hab'])}"
            ),
            "expected": "conteos=3; areas=5; pobreza=5; ipp=5",
            "detail": "La base queda utilizable para consultas analiticas basicas.",
        },
        {
            "check_id": "schema_disponible",
            "description": "`PRAGMA table_info` devuelve estructura para todas las tablas.",
            "is_valid": all(schema_info[table_name] for table_name in expected_tables),
            "observed": ", ".join(
                f"{table_name}={len(schema_info[table_name])}" for table_name in expected_tables
            ),
            "expected": "todas las tablas con al menos 1 columna",
            "detail": "La estructura fisica queda inspeccionable y documentada.",
        },
    ]

    report_markdown = build_sqlite_report_markdown(
        dataset_path=dataset_path,
        sqlite_path=sqlite_path,
        table_names=table_names,
        row_counts=row_counts,
        validation_checks=validation_checks,
        schema_info=schema_info,
        query_results=query_results,
        metadata_info=metadata_info,
    )
    export_sqlite_report_markdown(report_markdown)
    query_results_df = export_query_results_csv(
        query_results=query_results,
        duplicate_counts=duplicate_counts,
        coverage=coverage,
    )

    return {
        "sqlite_path": sqlite_path,
        "table_names": table_names,
        "row_counts": row_counts,
        "duplicate_counts": duplicate_counts,
        "coverage": coverage,
        "schema_info": schema_info,
        "query_results": query_results,
        "validation_checks": validation_checks,
        "report_markdown_path": REPORTE_CARGA_SQLITE_MD_PATH,
        "queries_csv_path": REPORTE_CONSULTAS_SQLITE_CSV_PATH,
        "query_results_df": query_results_df,
        "metadata_info": metadata_info,
        "phase_7_result": phase_7_result,
        "sqlite_reused": sqlite_reused,
    }


if __name__ == "__main__":
    result = run_phase_8_load()
    print(f"SQLite: {_relpath(result['sqlite_path'])}")
    for table_name, row_count in result["row_counts"].items():
        print(f"{table_name}: {row_count}")
