import sys
import os
import requests
from pathlib import Path

# Permite ejecutar el script directamente sin instalar el paquete
BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.db.session import SessionLocal
from app.repositories.sidpol_repository import SIDPOLCrimeRepository
from app.services.crime_analytics_service import CrimeAnalyticsService


def run_sidpol_ingestion():
    """
    Script principal para ingestar datos de criminalidad del SIDPOL.
    """
    db = SessionLocal()

    try:
        repo = SIDPOLCrimeRepository(db_session=db)

        # --- Paso 1: Descargar el archivo ---
        print("--- Paso 1: Descargando archivo SIDPOL ---")
        file_path = repo.download_source()

        if not os.path.exists(file_path):
            print(f"Descargando desde: {repo.source_url}")
            print("(esto puede tardar unos segundos...)")

            response = requests.get(repo.source_url, timeout=60, verify=False)
            response.raise_for_status()

            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "wb") as f:
                f.write(response.content)

            print(f"  -> Archivo guardado en: {file_path}")
        else:
            print(f"  -> Archivo ya existe en cache: {file_path}")

        # --- Paso 2: Parsear el archivo ---
        print("\n--- Paso 2: Parseando datos ---")
        summary_df = repo.parse_source(file_path)
        print(f"  -> {len(summary_df)} registros procesados")

        # --- Paso 3: Guardar datos crudos en crimen_raw_data ---
        print("\n--- Paso 3: Guardando en crimen_raw_data ---")
        repo.save_rates(summary_df)
        print("  -> Datos crudos guardados")

        # --- Paso 4: Calcular tasas normalizadas en district_crime_stats ---
        print("\n--- Paso 4: Calculando tasas normalizadas (district_crime_stats) ---")
        service = CrimeAnalyticsService(db=db)
        service.process_crime_metrics()

        print("\nListo. Puedes verificar con:")
        print("  SELECT district_name, weighted_crime_rate FROM district_crime_stats ORDER BY weighted_crime_rate DESC;")

    except requests.exceptions.RequestException as error:
        print(f"Error al descargar el archivo: {error}")
        print("Verifica que SIDPOL_SOURCE_URL esté configurada en el .env")
        raise
    except Exception as error:
        db.rollback()
        print(f"Error: {error}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_sidpol_ingestion()
