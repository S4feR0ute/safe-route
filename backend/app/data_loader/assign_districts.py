import sys
import time
from pathlib import Path

# Permite ejecutar el script directamente sin instalar el paquete
BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.constants import TARGET_DISTRICTS, UBIGEO_MAP
from app.db.session import SessionLocal
from app.models.district import District
from app.repositories.district_dao import OSMnxDistrictDAO
from app.services.segment_district_service import SegmentDistrictService


def run_district_assignment(districts=None):
    districts = districts or TARGET_DISTRICTS
    db = SessionLocal()

    ok_count = 0
    failed = []

    try:
        dao = OSMnxDistrictDAO(db_session=db)

        print("--- Paso 1: Cargar polígonos de distritos ---")
        print(f"Distritos a procesar: {len(districts)}")

        for index, place_name in enumerate(districts, 1):
            print(f"\n[{index}/{len(districts)}] {place_name}")
            try:
                # Obtener el ubigeo del mapa (si no está en el mapa, usamos el nombre)
                ubigeo = UBIGEO_MAP.get(place_name, place_name.split(",")[0].strip())

                boundary = dao.extract_boundary(place_name, ubigeo)

                if boundary is None:
                    failed.append((place_name, "Sin polígono en OSM"))
                    continue

                dao.save_boundary(boundary)
                ok_count += 1
                time.sleep(0.5)  # Para no saturar la API de OSM

            except Exception as error:
                db.rollback()
                failed.append((place_name, str(error)))
                print(f"  ERROR: {error}")

        db.commit()

        print(f"\nPolígonos cargados: {ok_count}/{len(districts)}")
        if failed:
            print("Distritos con error:")
            for name, msg in failed:
                print(f"  - {name}: {msg}")

        # --- Paso 2: Asignar distritos a segmentos con ST_Within ---
        print("\n--- Paso 2: Asignar distritos a segmentos (ST_Within) ---")
        service = SegmentDistrictService(db=db)
        total_actualizados = service.assign_districts_to_segments()

        # --- Paso 3: Mostrar resumen ---
        print("\n--- Resumen por distrito ---")
        resumen = service.get_resumen()
        for fila in resumen:
            print(f"  {fila.name} ({fila.ubigeo}): {fila.total_segmentos} segmentos")

        print(f"\nListo. Total segmentos con distrito asignado: {total_actualizados}")

    except Exception as error:
        db.rollback()
        print(f"Error crítico: {error}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_district_assignment()
