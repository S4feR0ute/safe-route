import sys
import time
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.constants import TARGET_DISTRICTS
from app.db.session import SessionLocal
from app.repositories.osmnx_context_dao import OSMnxContextDAO

POLICE_TAGS = {"amenity": "police"}
CAMERA_TAGS = {"man_made": "surveillance"}


def run_context_ingestion(districts=None):
    districts = districts or TARGET_DISTRICTS
    db = SessionLocal()

    ok_count = 0
    failed = []

    try:
        dao = OSMnxContextDAO(db_session=db)
        print("--- Ingesta de contexto urbano (OSMnx) ---")

        for index, district in enumerate(districts, 1):
            print(f"\n[{index}/{len(districts)}] {district}")
            try:
                police_gdf = dao.extract_pois(district, POLICE_TAGS)
                dao.save_pois(police_gdf, poi_type="police_station")

                camera_gdf = dao.extract_pois(district, CAMERA_TAGS)
                dao.save_pois(camera_gdf, poi_type="surveillance_camera")

                ok_count += 1
                time.sleep(1)
            except Exception as error:
                db.rollback()
                failed.append((district, str(error)))
                print(f"  ERROR: {error}")

        print("\n--- Resumen ---")
        print(f"Distritos OK: {ok_count}/{len(districts)}")
        if failed:
            print("Distritos con error:")
            for name, msg in failed:
                print(f"  - {name}: {msg}")

    except Exception as error:
        db.rollback()
        print(f"Error crítico: {error}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_context_ingestion()
