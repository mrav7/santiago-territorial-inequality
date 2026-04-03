from __future__ import annotations

import csv
import sys
from pathlib import Path

from config import (
    BASE_DIR,
    COBERTURA_TERRITORIAL,
    CONFLICTOS_FUENTES_PATH,
    DIM_COMUNA_BASE_PATH,
    DIM_COMUNA_BASE_REQUIRED_COLUMNS,
    FINAL_DATASET_PATH,
    HOMOLOGACION_COMUNAS_PATH,
    KEY_PATHS,
    LOG_INTEGRACION_PATH,
    METADATA_PATH,
    METADATA_REQUIRED_COLUMNS,
    PERFILADO_FUENTES_PATH,
    PROJECT_NAME,
    PROJECT_PHASE,
    PROJECT_TITLE,
    RAW_SOURCES,
    REQUIRED_DIRS,
    RESUMEN_DATASET_FINAL_PATH,
    RESUMEN_HOMOLOGACION_PATH,
    RESUMEN_TRANSFORMACIONES_PATH,
    STAGING_SOURCE_PATHS,
    TIPO_ANALISIS,
    UNIDAD_ANALISIS,
    VALIDACION_STAGING_PATH,
    ensure_directories,
)
from comunas import run_phase_3_master_key
from extract import run_phase_2_profile
from integrate import run_phase_6_integration
from transform import extract_all_to_staging
from validate import run_phase_5_validation


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
    print("Este proceso aun no genera SQLite ni cierra la validacion final del laboratorio.")
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
    print(
        "Resultado final: Fases 1 a 6 ejecutadas con dataset final integrado; "
        "SQLite y validacion final completa quedan pendientes para fases posteriores."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
