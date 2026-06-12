import os
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.core.constants import TARGET_DISTRICTS
from app.db.session import SessionLocal 
from app.repositories.osmnx_context_dao import OSMnxContextDAO

POLICE_TAGS = {'amenity': 'police'}
CAMERA_TAGS = {'man_made': 'surveillance'} 

def run_context_ingestion():
    db = SessionLocal()
    
    try:
        dao = OSMnxContextDAO(db_session=db)
        
        print("--- Starting Urban Context Ingestion ---")
        
        for index, district in enumerate(TARGET_DISTRICTS, 1):
            print(f"\n[{index}/{len(TARGET_DISTRICTS)}] Searching infrastructure in: {district}")
            
            try:
                # 1. Extraer y guardar Comisarías
                police_gdf = dao.extract_pois(district, POLICE_TAGS)
                dao.save_pois_to_db(police_gdf, poi_type="police_station")
                
                # 2. Extraer y guardar Cámaras de Seguridad
                camera_gdf = dao.extract_pois(district, CAMERA_TAGS)
                dao.save_pois_to_db(camera_gdf, poi_type="surveillance_camera")
                
                time.sleep(1)
                
            except Exception as e:
                print(f" ERROR processing '{district}': {e}")
                db.rollback()
                continue
                
        print("\n--- Urban Context Ingestion Completed ---")

    except Exception as e:
        print(f"A critical error occurred: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run_context_ingestion()