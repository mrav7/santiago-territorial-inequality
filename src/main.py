from config import ensure_directories


def main() -> None:
    ensure_directories()
    print("Estructura verificada.")
    print("Proyecto listo para iniciar perfilado y extracción de fuentes.")


if __name__ == "__main__":
    main()