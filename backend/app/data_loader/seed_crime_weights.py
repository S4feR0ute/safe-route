import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.db.session import SessionLocal
from app.models.crime_type_weight import CrimeTypeWeight
from app.core.constants import CRIME_WEIGHTS_MAP, STREET_CRIMES

def run_seed_crime_weights():
    """
    Puebla la tabla crime_types_weights con los pesos definidos en CRIME_WEIGHTS_MAP.
    """
    db = SessionLocal()

    try:
        print("--- Seed: pesos por tipo de delito ---")

        insertados = 0
        actualizados = 0

        for crime_type, weight in CRIME_WEIGHTS_MAP.items():
            existing = db.query(CrimeTypeWeight).filter(
                CrimeTypeWeight.subtype_name == crime_type
            ).first()

            is_street = crime_type in STREET_CRIMES

            if existing:
                existing.danger_weight = weight
                existing.is_street_crime = is_street
                actualizados += 1
            else:
                nuevo = CrimeTypeWeight(
                    subtype_name=crime_type,
                    danger_weight=weight,
                    is_street_crime=is_street,
                )
                db.add(nuevo)
                insertados += 1

        db.commit()

        print(f"  -> {insertados} tipos insertados, {actualizados} actualizados")
        print("\nPesos cargados:")

        todos = db.query(CrimeTypeWeight).order_by(CrimeTypeWeight.danger_weight.desc()).all()
        for entry in todos:
            calle = "callejero" if entry.is_street_crime else "interior"
            print(f"  [{entry.danger_weight:.2f}] {entry.subtype_name} ({calle})")

    except Exception as error:
        db.rollback()
        print(f"Error: {error}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_seed_crime_weights()
