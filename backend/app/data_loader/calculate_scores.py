import sys
from pathlib import Path

# Permite ejecutar el script directamente sin instalar el paquete
BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.db.session import SessionLocal
from app.db.transactions import transaction
from app.models.street_network import StreetSegment, StreetNode  # necesario para que SQLAlchemy registre la tabla antes del commit
from app.models.risk_score import RiskScore
from app.services.score_calculator_service import ScoreCalculatorService


def run_score_calculation():
    """Script principal para calcular el score compuesto de todos los segmentos."""
    db = SessionLocal()

    with transaction(db):
        print("=== Score Calculator ===")
        service = ScoreCalculatorService(db=db)
        total = service.calculate_all_scores()

        if total > 0:
            print(f"\nListo. {total} segmentos con composite_score calculado.")
            print("Puedes verificar con:")
            print("  SELECT AVG(composite_score), MIN(composite_score), MAX(composite_score)")
            print("  FROM risk_scores;")


if __name__ == "__main__":
    run_score_calculation()
