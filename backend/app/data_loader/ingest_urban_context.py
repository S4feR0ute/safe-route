import sys
import time
import logging
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.constants import TARGET_DISTRICTS
from app.db.session import SessionLocal
from app.db.transactions import transaction_no_close
from app.repositories.osmnx_context_dao import OSMnxContextDAO

logger = logging.getLogger(__name__)

POLICE_TAGS = {"amenity": "police"}
CAMERA_TAGS = {"man_made": "surveillance"}
BANK_TAGS = {"amenity": "bank"}
LIGHTING_TAGS = {"highway": "street_lamp"}

SHOP_TAGS = {"shop": True}  # Todos los valores
AMENITY_RESTAURANT_TAGS = {"amenity": ["restaurant", "cafe", "bar", "fast_food"]}
PHARMACY_TAGS = {"amenity": "pharmacy"}
FUEL_TAGS = {"amenity": "fuel"}
MARKET_TAGS = {"amenity": "marketplace"}


def run_context_ingestion(districts=None):
    districts = districts or TARGET_DISTRICTS
    db = SessionLocal()

    ok_count = 0
    failed = []

    try:
        with transaction_no_close(db):
            dao = OSMnxContextDAO(db=db)
            logger.info("--- Ingesta de contexto urbano (OSMnx) ---")

            for index, district in enumerate(districts, 1):
                logger.info(f"\n[{index}/{len(districts)}] {district}")
                try:
                    # Presencia policial
                    police_gdf = dao.extract_pois(district, POLICE_TAGS)
                    dao.save_pois(police_gdf, poi_type="police_station")
                    logger.info(f"  ✓ {len(police_gdf)} comisarías")

                    # Vigilancia - Cámaras
                    # camera_gdf = dao.extract_pois(district, CAMERA_TAGS)
                    # dao.save_pois(camera_gdf, poi_type="surveillance_camera")
                    # print(f"  ✓ {len(camera_gdf)} cámaras de vigilancia")

                    # Vigilancia - Bancos
                    bank_gdf = dao.extract_pois(district, BANK_TAGS)
                    dao.save_pois(bank_gdf, poi_type="bank")
                    logger.info(f"  ✓ {len(bank_gdf)} bancos")

                    # Iluminación - Postes de luz
                    # lighting_gdf = dao.extract_pois(district, LIGHTING_TAGS)
                    # dao.save_pois(lighting_gdf, poi_type="street_lamp")
                    # print(f"  ✓ {len(lighting_gdf)} postes de luz")

                    # Comercio - Tiendas
                    # shop_gdf = dao.extract_pois(district, SHOP_TAGS)
                    # dao.save_pois(shop_gdf, poi_type="shop")
                    # print(f"  ✓ {len(shop_gdf)} tiendas")

                    # Comercio - Restaurantes, cafeterías, bares
                    # restaurant_gdf = dao.extract_pois(district, AMENITY_RESTAURANT_TAGS)
                    # dao.save_pois(restaurant_gdf, poi_type="restaurant")
                    # print(f"  ✓ {len(restaurant_gdf)} restaurantes/cafeterías/bares")

                    # Comercio - Farmacias
                    # pharmacy_gdf = dao.extract_pois(district, PHARMACY_TAGS)
                    # dao.save_pois(pharmacy_gdf, poi_type="pharmacy")
                    # print(f"  ✓ {len(pharmacy_gdf)} farmacias")

                    # Comercio - Gasolineras
                    # fuel_gdf = dao.extract_pois(district, FUEL_TAGS)
                    # dao.save_pois(fuel_gdf, poi_type="fuel")
                    # print(f"  ✓ {len(fuel_gdf)} gasolineras")

                    # Comercio - Mercados
                    # market_gdf = dao.extract_pois(district, MARKET_TAGS)
                    # dao.save_pois(market_gdf, poi_type="marketplace")
                    # print(f"  ✓ {len(market_gdf)} mercados")

                    ok_count += 1
                    db.commit()
                    time.sleep(1)
                except Exception as error:
                    db.rollback()
                    failed.append((district, str(error)))
                    logger.info(f"  ERROR: {error}")

            logger.info("\n--- Resumen ---")
            logger.info(f"Distritos OK: {ok_count}/{len(districts)}")
            if failed:
                logger.info("Distritos con error:")
                for name, msg in failed:
                    logger.info(f"  - {name}: {msg}")

    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    run_context_ingestion()
