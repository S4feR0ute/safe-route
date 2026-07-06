import sys
import logging
from pathlib import Path

# Permite ejecutar el script directamente sin instalar el paquete
BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.db.session import SessionLocal
from app.db.transactions import transaction
from app.services.score_calculator_service import ScoreCalculatorService

logger = logging.getLogger(__name__)


def run_score_calculation():
    """Script principal para calcular el score compuesto de todos los segmentos."""
    db = SessionLocal()

    with transaction(db):
        logger.info("=== Score Calculator ===")
        service = ScoreCalculatorService(db=db)
        total = service.calculate_all_scores()

        if total > 0:
            logger.info(f"Listo. {total} segmentos con composite_score calculado.")
            logger.info("Puedes verificar con:")
            logger.info("  SELECT AVG(composite_score), MIN(composite_score), MAX(composite_score) FROM risk_scores;")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    run_score_calculation()
