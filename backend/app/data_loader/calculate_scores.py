import sys
from pathlib import Path

# Permite ejecutar el script directamente sin instalar el paquete
BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.db.session import SessionLocal
from app.services.score_calculator_service import ScoreCalculatorService


def run_score_calculation():
    """
    Script principal para calcular el score compuesto de todos los segmentos.

    Prerrequisitos (deben haberse ejecutado antes):
        1. ingest_street_graph.py   -> tabla street_segments con geometrías
        2. assign_districts.py      -> district_ubigeo asignado a cada segmento
        3. ingest_sidpol            -> tabla district_crime_stats con tasas normalizadas
        4. ingest_urban_context.py  -> tabla urban_pois con comisarías y cámaras
    """
    db = SessionLocal()

    try:
        print("=== Score Calculator (RF-09) ===")
        service = ScoreCalculatorService(db=db)
        total = service.calculate_all_scores()

        if total > 0:
            print(f"\nListo. {total} segmentos con composite_score calculado.")
            print("Puedes verificar con:")
            print("  SELECT AVG(composite_score), MIN(composite_score), MAX(composite_score)")
            print("  FROM risk_scores;")

    except Exception as error:
        db.rollback()
        print(f"Error: {error}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_score_calculation()
