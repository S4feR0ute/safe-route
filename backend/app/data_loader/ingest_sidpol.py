import sys
import logging
import requests
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.db.session import SessionLocal
from app.db.transactions import transaction
from app.repositories.sidpol_dao import SIDPOLCrimeDAO
from app.services.crime_analytics_service import CrimeAnalyticsService

logger = logging.getLogger(__name__)


def run_sidpol_ingestion():
    """
    Script principal para ingestar datos de criminalidad del SIDPOL.
    """
    db = SessionLocal()

    try:
        with transaction(db):
            dao = SIDPOLCrimeDAO(db=db)

            logger.info("Descargando archivo SIDPOL")
            file_path = dao.download_source()

            logger.info("Parseando datos")
            summary_df = dao.parse_source(file_path)
            logger.info(f"{len(summary_df)} registros procesados")

            logger.info("Guardando en crime_raw_data")
            dao.save_rates(summary_df)

            logger.info("Calculando tasas normalizadas")
            service = CrimeAnalyticsService(db=db)
            service.process_crime_metrics()
            logger.info("Ingesta completada")

    except requests.exceptions.RequestException as error:
        logger.error(f"Error descargando: {error}")
        raise


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    run_sidpol_ingestion()
