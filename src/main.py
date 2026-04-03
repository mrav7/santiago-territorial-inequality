from __future__ import annotations

import csv
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import (
    ANALISIS_EXPLORATORIO_MD_PATH,
    AREAS_VERDES_BOTTOM10_FIGURE_PATH,
    BASE_DIR,
    COBERTURA_TERRITORIAL,
    CONFLICTOS_FUENTES_PATH,
    DIM_COMUNA_BASE_PATH,
    DIM_COMUNA_BASE_REQUIRED_COLUMNS,
    FINAL_DATASET_PATH,
    HOMOLOGACION_COMUNAS_PATH,
    INDICE_REZAGO_TOP10_FIGURE_PATH,
    IPP_BOTTOM10_FIGURE_PATH,
    KEY_PATHS,
    LOG_INTEGRACION_PATH,
    METADATA_PATH,
    METADATA_REQUIRED_COLUMNS,
    PERFILADO_FUENTES_PATH,
    POBREZA_AREAS_SCATTER_FIGURE_PATH,
    POBREZA_TOP10_FIGURE_PATH,
    PROJECT_NAME,
    PROJECT_PHASE,
    PROJECT_TITLE,
    RAW_SOURCES,
    RANKING_AREAS_VERDES_CSV_PATH,
    RANKING_IPP_CSV_PATH,
    RANKING_POBREZA_CSV_PATH,
    REPORTE_CARGA_SQLITE_MD_PATH,
    REPORTE_CONSULTAS_SQLITE_CSV_PATH,
    REPORTE_VALIDACION_FINAL_CSV_PATH,
    REPORTE_VALIDACION_FINAL_MD_PATH,
    REQUIRED_DIRS,
    RESUMEN_DATASET_FINAL_PATH,
    RESUMEN_HOMOLOGACION_PATH,
    RESUMEN_TRANSFORMACIONES_PATH,
    SQLITE_PATH,
    STAGING_SOURCE_PATHS,
    TABLAS_HALLAZGOS_FASE9_CSV_PATH,
    TIPO_ANALISIS,
    UNIDAD_ANALISIS,
    VALIDACION_STAGING_PATH,
    ensure_directories,
)
from src.analyze import run_phase_9_analysis
from src.comunas import run_phase_3_master_key
from src.extract import run_phase_2_profile
from src.integrate import run_phase_6_integration
from src.load import run_phase_8_load
from src.transform import extract_all_to_staging
from src.validate import run_phase_5_validation, run_phase_7_validation


def relpath(path: Path) -> str:
    """Devuelve una ruta relativa al repositorio para reportes legibles."""
    return path.relative_to(BASE_DIR).as_posix()


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def validate_directories(errors: list[str]) -> list[str]:
    statuses: list[str] = []
    for directory in REQUIRED_DIRS:
        if directory.is_dir():
            statuses.append(f"[OK] Directorio presente: {relpath(directory)}")
        else:
            errors.append(f"Falta el directorio requerido: {relpath(directory)}")
            statuses.append(f"[ERROR] Directorio ausente: {relpath(directory)}")
    return statuses


def validate_key_paths(errors: list[str]) -> list[str]:
    statuses: list[str] = []
    for path in KEY_PATHS:
        if path.exists():
            statuses.append(f"[OK] Ruta clave presente: {relpath(path)}")
        else:
            errors.append(f"Falta la ruta clave: {relpath(path)}")
            statuses.append(f"[ERROR] Ruta clave ausente: {relpath(path)}")
    return statuses


def validate_dim_comuna_base(errors: list[str]) -> list[str]:
    statuses: list[str] = []
    if not DIM_COMUNA_BASE_PATH.exists():
        errors.append(f"No existe {relpath(DIM_COMUNA_BASE_PATH)}")
        return [f"[ERROR] Archivo ausente: {relpath(DIM_COMUNA_BASE_PATH)}"]

    rows = read_csv_rows(DIM_COMUNA_BASE_PATH)
    if not rows:
        errors.append("dim_comuna_base.csv esta vacio")
        return [f"[ERROR] Archivo vacio: {relpath(DIM_COMUNA_BASE_PATH)}"]

    header = tuple(rows[0].keys())
    if header != DIM_COMUNA_BASE_REQUIRED_COLUMNS:
        errors.append(
            "dim_comuna_base.csv no tiene las columnas esperadas: "
            f"{DIM_COMUNA_BASE_REQUIRED_COLUMNS}"
        )
        statuses.append(
            "[ERROR] dim_comuna_base.csv tiene columnas distintas a las esperadas."
        )
    else:
        statuses.append(
            "[OK] dim_comuna_base.csv tiene las columnas esperadas."
        )

    if len(rows) != 32:
        errors.append(
            "dim_comuna_base.csv deberia contener 32 comunas de la Provincia de "
            f"Santiago y contiene {len(rows)}."
        )
        statuses.append(
            f"[ERROR] dim_comuna_base.csv contiene {len(rows)} filas; se esperaban 32."
        )
    else:
        statuses.append(
            "[OK] dim_comuna_base.csv contiene 32 comunas de la Provincia de Santiago."
        )

    return statuses


def validate_metadata(errors: list[str]) -> list[str]:
    statuses: list[str] = []
    if not METADATA_PATH.exists():
        errors.append(f"No existe {relpath(METADATA_PATH)}")
        return [f"[ERROR] Archivo ausente: {relpath(METADATA_PATH)}"]

    rows = read_csv_rows(METADATA_PATH)
    if not rows:
        errors.append("metadata_fuentes.csv esta vacio")
        return [f"[ERROR] Archivo vacio: {relpath(METADATA_PATH)}"]

    header = tuple(rows[0].keys())
    if header != METADATA_REQUIRED_COLUMNS:
        errors.append(
            "metadata_fuentes.csv no tiene las columnas esperadas: "
            f"{METADATA_REQUIRED_COLUMNS}"
        )
        statuses.append(
            "[ERROR] metadata_fuentes.csv tiene una estructura de columnas distinta."
        )
        return statuses

    statuses.append("[OK] metadata_fuentes.csv tiene la estructura esperada.")

    rows_by_id = {row["id_fuente"]: row for row in rows}
    expected_ids = tuple(RAW_SOURCES.keys())
    if tuple(rows_by_id.keys()) != expected_ids:
        errors.append(
            "metadata_fuentes.csv debe documentar exactamente las fuentes "
            f"{expected_ids} y hoy contiene {tuple(rows_by_id.keys())}."
        )
        statuses.append(
            "[ERROR] metadata_fuentes.csv no documenta exactamente las fuentes A-D."
        )

    for source_id, source_data in RAW_SOURCES.items():
        row = rows_by_id.get(source_id)
        if row is None:
            errors.append(f"Falta la fuente {source_id} en metadata_fuentes.csv")
            statuses.append(f"[ERROR] Falta la fuente {source_id} en metadata_fuentes.csv.")
            continue

        expected_path = source_data["archivo_origen"]
        expected_logical_name = source_data["archivo_logico"]
        expected_sheet = source_data["hoja"]
        expected_skiprows = str(source_data["skiprows"])

        actual_values = {
            "archivo_origen": row["archivo_origen"],
            "archivo_logico": row["archivo_logico"],
            "hoja": row["hoja"],
            "skiprows": row["skiprows"],
        }
        expected_values = {
            "archivo_origen": expected_path,
            "archivo_logico": expected_logical_name,
            "hoja": expected_sheet,
            "skiprows": expected_skiprows,
        }

        mismatches = [
            field_name
            for field_name, expected_value in expected_values.items()
            if actual_values[field_name] != expected_value
        ]

        if mismatches:
            errors.append(
                f"Fuente {source_id} en metadata_fuentes.csv tiene diferencias en: "
                f"{', '.join(mismatches)}."
            )
            statuses.append(
                f"[ERROR] Fuente {source_id} con metadata inconsistente en "
                f"{', '.join(mismatches)}."
            )
        else:
            statuses.append(
                f"[OK] Fuente {source_id} consistente: archivo, hoja y skiprows validados."
            )

        referenced_path = BASE_DIR / row["archivo_origen"]
        if not referenced_path.exists():
            errors.append(
                f"La fuente {source_id} referencia un archivo inexistente: "
                f"{row['archivo_origen']}"
            )
            statuses.append(
                f"[ERROR] La fuente {source_id} apunta a un archivo que no existe."
            )

    return statuses


def print_section(title: str, items: list[str]) -> None:
    print(title)
    for item in items:
        print(f"  {item}")


def main() -> int:
    ensure_directories()

    errors: list[str] = []
    print(f"{PROJECT_PHASE} - {PROJECT_NAME}")
    print(PROJECT_TITLE)
    print(f"Unidad de analisis: {UNIDAD_ANALISIS}")
    print(f"Cobertura: {COBERTURA_TERRITORIAL}")
    print(f"Tipo de analisis: {TIPO_ANALISIS}")
    print()
    print("Paso 1: verificacion de base heredada desde Fase 1.")
    print("Paso 2: lectura real y perfilado diagnostico de las cuatro fuentes.")
    print("Paso 3: validacion de base maestra comunal y homologacion reproducible.")
    print("Paso 4: extraccion reproducible a staging por fuente.")
    print("Paso 5: transformacion y validacion de staging por fuente.")
    print("Paso 6: integracion del dataset final comunal desde staging.")
    print("Paso 7: validacion formal del dataset final integrado.")
    print("Paso 8: carga final a SQLite y validacion formal de la base resultante.")
    print("Paso 9: analisis exploratorio reproducible y outputs para comunicar.")
    print()

    print_section("Estructura minima", validate_directories(errors))
    print()
    print_section("Rutas clave", validate_key_paths(errors))
    print()
    print_section("Dimension base", validate_dim_comuna_base(errors))
    print()
    print_section("Metadata y fuentes", validate_metadata(errors))
    print()

    if errors:
        print(f"Resultado: preflight con errores ({len(errors)}).")
        for error in errors:
            print(f"- {error}")
        print("Base de Fase 1 aun no verificada.")
        return 1

    print("Resultado preflight: validaciones completadas sin errores.")
    print("Base de Fase 1 verificada.")
    print()

    phase_2_result = run_phase_2_profile()
    print("Fase 2 - Perfilado y diagnostico")
    for source_id, dataset in phase_2_result["datasets"].items():
        print(
            f"  [OK] Fuente {source_id}: {len(dataset.dataframe)} filas, "
            f"{len(dataset.dataframe.columns)} columnas, parser={dataset.diagnostics['source_parser']}"
        )
    print()
    print(f"Output perfilado: {PERFILADO_FUENTES_PATH.relative_to(BASE_DIR).as_posix()}")
    print(f"Output conflictos: {CONFLICTOS_FUENTES_PATH.relative_to(BASE_DIR).as_posix()}")
    print("Hallazgos clave:")
    for highlight in phase_2_result["highlights"]:
        print(f"  - {highlight}")
    print()

    phase_3_result = run_phase_3_master_key(datasets=phase_2_result["datasets"])
    print("Fase 3 - Llave maestra comunal")
    for status in phase_3_result["validation"].statuses:
        print(f"  {status}")
    for warning in phase_3_result["validation"].warnings:
        print(f"  [OBSERVACION] {warning}")
    print(f"  Politica de llave: {phase_3_result['master_key_policy']}")
    print()
    print(
        f"Output homologacion: {HOMOLOGACION_COMUNAS_PATH.relative_to(BASE_DIR).as_posix()}"
    )
    print(
        f"Output resumen homologacion: {RESUMEN_HOMOLOGACION_PATH.relative_to(BASE_DIR).as_posix()}"
    )
    print("Resumen por fuente:")
    for _, row in phase_3_result["summary_df"].iterrows():
        print(
            "  - Fuente {fuente}: exactas={coincidencias_exactas}, "
            "normalizacion={coincidencias_por_normalizacion}, "
            "manuales={requieren_homologacion_manual}, "
            "fuera_de_alcance={fuera_universo_final}".format(**row.to_dict())
        )
    print()

    phase_45_result = extract_all_to_staging(
        datasets=phase_2_result["datasets"],
        dim_base=phase_3_result["master_dimension"],
    )
    print("Fase 4 y Fase 5 - Staging por fuente")
    for source_id, artifact in phase_45_result["artifacts"].items():
        print(
            f"  [OK] Fuente {source_id}: {artifact.row_count} filas, "
            f"{artifact.column_count} columnas -> "
            f"{artifact.path.relative_to(BASE_DIR).as_posix()}"
        )
    print()

    validation_result = run_phase_5_validation(
        staging_tables=phase_45_result["staging_tables"],
        dim_base=phase_3_result["master_dimension"],
        artifacts=phase_45_result["artifacts"],
        evidences=phase_45_result["evidences"],
    )
    print("Validacion de staging")
    for source_id, artifact in phase_45_result["artifacts"].items():
        status = validation_result["validation_results"][source_id]
        label = "[OK]" if status.is_valid else "[ERROR]"
        print(
            f"  {label} Fuente {source_id}: {artifact.row_count} filas, "
            f"{artifact.column_count} columnas -> "
            f"{artifact.path.relative_to(BASE_DIR).as_posix()}"
        )
        for warning in status.warnings:
            print(f"    [OBSERVACION] {warning}")
    print()
    print("Outputs staging:")
    for source_id in sorted(STAGING_SOURCE_PATHS):
        print(f"  - Fuente {source_id}: {STAGING_SOURCE_PATHS[source_id].relative_to(BASE_DIR).as_posix()}")
    print(f"Resumen transformaciones: {RESUMEN_TRANSFORMACIONES_PATH.relative_to(BASE_DIR).as_posix()}")
    print(f"Validacion staging: {VALIDACION_STAGING_PATH.relative_to(BASE_DIR).as_posix()}")
    print()

    phase_6_result = run_phase_6_integration()
    print("Fase 6 - Integracion y dataset final")
    for evidence in phase_6_result["merge_evidences"]:
        print(
            f"  [OK] Merge {evidence.source_id} ({evidence.source_label}): "
            f"{evidence.rows_before} -> {evidence.rows_after} filas; "
            f"columnas incorporadas: {', '.join(evidence.added_columns)}"
        )
    print(
        f"  [OK] Dataset final: {phase_6_result['validation']['row_count']} filas, "
        f"{phase_6_result['validation']['column_count']} columnas -> "
        f"{FINAL_DATASET_PATH.relative_to(BASE_DIR).as_posix()}"
    )
    print()
    print("Outputs Fase 6:")
    print(f"  - Dataset final: {FINAL_DATASET_PATH.relative_to(BASE_DIR).as_posix()}")
    print(f"  - Log de integracion: {LOG_INTEGRACION_PATH.relative_to(BASE_DIR).as_posix()}")
    print(
        f"  - Resumen dataset final: {RESUMEN_DATASET_FINAL_PATH.relative_to(BASE_DIR).as_posix()}"
    )
    print()
    phase_7_result = run_phase_7_validation(
        dim_base=phase_3_result["master_dimension"],
        dataset_path=FINAL_DATASET_PATH,
    )
    final_validation = phase_7_result["validation_result"]
    print("Fase 7 - Validacion formal del dataset final")
    for check in final_validation.checks:
        print(
            f"  [{'OK' if check.is_valid else 'ERROR'}] {check.check_id}: "
            f"{check.observed_value}"
        )
    print()
    print("Outputs Fase 7:")
    print(
        f"  - Reporte CSV: {REPORTE_VALIDACION_FINAL_CSV_PATH.relative_to(BASE_DIR).as_posix()}"
    )
    print(
        f"  - Reporte Markdown: {REPORTE_VALIDACION_FINAL_MD_PATH.relative_to(BASE_DIR).as_posix()}"
    )
    print()
    print(
        "Resultado parcial: Fases 1 a 7 ejecutadas; el dataset final queda "
        f"{'apto' if final_validation.is_valid else 'no apto'} para pasar a SQLite."
    )
    print()

    phase_8_result = run_phase_8_load(
        final_df=phase_6_result["final_dataset"],
        dim_base=phase_3_result["master_dimension"],
        dataset_path=FINAL_DATASET_PATH,
    )
    print("Fase 8 - Carga final a SQLite")
    for table_name, row_count in phase_8_result["row_counts"].items():
        print(f"  [OK] Tabla {table_name}: {row_count} filas")
    print(
        "  [OK] Cobertura dim/fact: "
        f"fact_sin_dim={phase_8_result['coverage']['fact_without_dim']}; "
        f"dim_sin_fact={phase_8_result['coverage']['dim_without_fact']}"
    )
    print(
        "  [OK] Base SQLite generada: "
        f"{SQLITE_PATH.relative_to(BASE_DIR).as_posix()}"
    )
    print()
    print("Outputs Fase 8:")
    print(f"  - SQLite: {SQLITE_PATH.relative_to(BASE_DIR).as_posix()}")
    print(
        f"  - Reporte de carga: {REPORTE_CARGA_SQLITE_MD_PATH.relative_to(BASE_DIR).as_posix()}"
    )
    print(
        "  - Reporte de consultas: "
        f"{REPORTE_CONSULTAS_SQLITE_CSV_PATH.relative_to(BASE_DIR).as_posix()}"
    )
    print()

    phase_9_result = run_phase_9_analysis(
        final_df=phase_6_result["final_dataset"],
        dataset_path=FINAL_DATASET_PATH,
        sqlite_path=SQLITE_PATH,
    )
    print("Fase 9 - Analisis exploratorio y hallazgos")
    consistency_result = phase_9_result["consistency_result"]
    print(
        "  [OK] Consistencia CSV/SQLite: "
        f"filas_csv={consistency_result['csv_rows']}; "
        f"filas_sqlite={consistency_result['sqlite_rows']}; "
        f"csv_only={list(consistency_result['csv_only_codes'])}; "
        f"sqlite_only={list(consistency_result['sqlite_only_codes'])}"
    )
    print(
        "  [OK] Comunas rezagadas en al menos dos dimensiones: "
        f"{len(phase_9_result['cross_tables']['rezagadas_en_dos_o_mas_dimensiones'])}"
    )
    print(
        "  [OK] Reporte analitico: "
        f"{ANALISIS_EXPLORATORIO_MD_PATH.relative_to(BASE_DIR).as_posix()}"
    )
    print()
    print("Outputs Fase 9:")
    print(
        f"  - Analisis exploratorio: {ANALISIS_EXPLORATORIO_MD_PATH.relative_to(BASE_DIR).as_posix()}"
    )
    print(
        f"  - Tablas de hallazgos: {TABLAS_HALLAZGOS_FASE9_CSV_PATH.relative_to(BASE_DIR).as_posix()}"
    )
    print(
        f"  - Ranking areas verdes: {RANKING_AREAS_VERDES_CSV_PATH.relative_to(BASE_DIR).as_posix()}"
    )
    print(
        f"  - Ranking pobreza: {RANKING_POBREZA_CSV_PATH.relative_to(BASE_DIR).as_posix()}"
    )
    print(
        f"  - Ranking IPP: {RANKING_IPP_CSV_PATH.relative_to(BASE_DIR).as_posix()}"
    )
    print(
        "  - Figura areas verdes: "
        f"{AREAS_VERDES_BOTTOM10_FIGURE_PATH.relative_to(BASE_DIR).as_posix()}"
    )
    print(
        f"  - Figura pobreza: {POBREZA_TOP10_FIGURE_PATH.relative_to(BASE_DIR).as_posix()}"
    )
    print(
        f"  - Figura IPP: {IPP_BOTTOM10_FIGURE_PATH.relative_to(BASE_DIR).as_posix()}"
    )
    print(
        "  - Figura scatter pobreza/areas: "
        f"{POBREZA_AREAS_SCATTER_FIGURE_PATH.relative_to(BASE_DIR).as_posix()}"
    )
    print(
        "  - Figura indice de rezago: "
        f"{INDICE_REZAGO_TOP10_FIGURE_PATH.relative_to(BASE_DIR).as_posix()}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
