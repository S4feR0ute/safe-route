import sys
import os
import logging
import requests
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.db.session import SessionLocal
from app.db.transactions import transaction
from app.repositories.sidpol_repository import SIDPOLCrimeRepository
from app.services.crime_analytics_service import CrimeAnalyticsService

logger = logging.getLogger(__name__)


def run_sidpol_ingestion():
    """
    Script principal para ingestar datos de criminalidad del SIDPOL.
    """
    db = SessionLocal()

    try:
        with transaction(db):
            repo = SIDPOLCrimeRepository(db=db)

            logger.info("Descargando archivo SIDPOL")
            file_path = repo.download_source()

            if not os.path.exists(file_path):
                logger.info(f"Descargando desde: {repo.source_url}")
                response = requests.get(repo.source_url, timeout=60, verify=False)
                response.raise_for_status()

                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, "wb") as f:
                    f.write(response.content)
                logger.info(f"Archivo guardado: {file_path}")
            else:
                logger.info(f"Usando cache: {file_path}")

            logger.info("Parseando datos")
            summary_df = repo.parse_source(file_path)
            logger.info(f"{len(summary_df)} registros procesados")

            logger.info("Guardando en crimen_raw_data")
            repo.save_rates(summary_df)

            logger.info("Calculando tasas normalizadas")
            service = CrimeAnalyticsService(db=db)
            service.process_crime_metrics()
            logger.info("Ingesta completada")

    except requests.exceptions.RequestException as error:
        logger.error(f"Error descargando: {error}")
        raise


if __name__ == "__main__":
    run_sidpol_ingestion()
