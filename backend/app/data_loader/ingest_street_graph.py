import sys
import time
from pathlib import Path
from sqlalchemy import text 

# Permite ejecutar el script directamente sin instalar el paquete
BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.constants import TARGET_DISTRICTS
from app.db.session import SessionLocal
from app.models.street_network import StreetNode, StreetSegment
from app.repositories.osmnx_street_graph_dao import OSMnxStreetGraphDAO


def run_street_network_ingestion(districts=None, network_type="walk"):
    districts = districts or TARGET_DISTRICTS
    db = SessionLocal()

    ok_count = 0
    failed = []
    total_segments = 0

    try:
        dao = OSMnxStreetGraphDAO(db_session=db, network_type=network_type)

        print("Limpiando tablas de red vial (vía TRUNCATE)...")
        db.execute(text("TRUNCATE TABLE street_segments, street_nodes RESTART IDENTITY CASCADE;"))
        db.commit()

        print(" Ingesta de red vial (OSMnx) ")
        print(f"Distritos a procesar: {len(districts)} | network_type={network_type}")

        for index, district in enumerate(districts, 1):
            print(f"\n[{index}/{len(districts)}] {district}")
            try:
                graph = dao.extract_graph(district)
                inserted = dao.save_graph(graph, district)
                total_segments += inserted
                ok_count += 1
                time.sleep(1)
            except Exception as error:
                db.rollback()
                failed.append((district, str(error)))
                print(f"  ERROR: {error}")

        print("\n Resumen ")
        print(f"Distritos OK: {ok_count}/{len(districts)}")
        print(f"Segmentos insertados: {total_segments}")
        if failed:
            print("Distritos con error:")
            for name, msg in failed:
                print(f"  - {name}: {msg}")
        
        # Asignar segmentos a distritos vía ST_Within
        print("\n Asignación de segmentos a distritos ")
        stats = dao.assign_segments_to_districts_st_within()
        
        print("\n Ingesta completada exitosamente")

    except Exception as error:
        db.rollback()
        print(f"Error crítico en la ingesta: {error}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_street_network_ingestion()