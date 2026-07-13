import sys
import time
import logging
from pathlib import Path

# Permite ejecutar el script directamente sin instalar el paquete
BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.constants import TARGET_DISTRICTS, UBIGEO_MAP
from app.db.session import SessionLocal
from app.db.transactions import transaction_no_close
from app.repositories.district_dao import OSMnxDistrictDAO
from app.services.segment_district_service import SegmentDistrictService

logger = logging.getLogger(__name__)


def run_district_assignment(districts=None):
    districts = districts or TARGET_DISTRICTS
    db = SessionLocal()

    ok_count = 0
    failed = []

    try:
        with transaction_no_close(db):
            dao = OSMnxDistrictDAO(db=db)

            logger.info("--- Paso 1: Cargar polígonos de distritos ---")
            logger.info(f"Distritos a procesar: {len(districts)}")

            for index, place_name in enumerate(districts, 1):
                logger.info(f"\n[{index}/{len(districts)}] {place_name}")
                try:
                    # Obtener el ubigeo del mapa (si no está en el mapa, usamos el nombre)
                    ubigeo = UBIGEO_MAP.get(place_name, place_name.split(",")[0].strip())

                    boundary = dao.extract_boundary(place_name, ubigeo)

                    if boundary is None:
                        failed.append((place_name, "Sin polígono en OSM"))
                        continue

                    dao.save_boundary(boundary)
                    ok_count += 1
                    db.commit()
                    time.sleep(0.5)  # Para no saturar la API de OSM

                except Exception as error:
                    db.rollback()
                    failed.append((place_name, str(error)))
                    logger.info(f"  ERROR: {error}")

            logger.info(f"\nPolígonos cargados: {ok_count}/{len(districts)}")
            if failed:
                logger.info("Distritos con error:")
                for name, msg in failed:
                    logger.info(f"  - {name}: {msg}")

            # --- Paso 2: Asignar distritos a segmentos con ST_Within ---
            logger.info("\n--- Paso 2: Asignar distritos a segmentos (ST_Within) ---")
            service = SegmentDistrictService(db=db)
            total_actualizados = service.assign_districts_to_segments()
            db.commit()

            # --- Paso 3: Mostrar resumen ---
            logger.info("\n--- Resumen por distrito ---")
            resumen = service.get_summary()
            for fila in resumen:
                logger.info(f"  {fila.name} ({fila.ubigeo}): {fila.total_segmentos} segmentos")

            logger.info(f"\nListo. Total segmentos con distrito asignado: {total_actualizados}")

    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    run_district_assignment()
