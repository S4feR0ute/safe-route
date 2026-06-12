import os
import sys
from time import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.models.street_network import StreetNode, StreetSegment
from app.db.session import SessionLocal 
from app.core.constants import TARGET_DISTRICTS
from app.repositories.osmnx_street_graph_dao import OSMnxStreetGraphDAO

def run_street_network_ingestion():

    db = SessionLocal()
    
    try:
        dao = OSMnxStreetGraphDAO(db_session=db, network_type='drive')
        
        print("Limpiando tablas de red vial antiguas...")
        db.query(StreetSegment).delete()
        db.query(StreetNode).delete()
        db.flush()

        successful_districts = 0
        failed_districts = []

        print("--- Iniciando Módulo de Ingesta de Red Vial ---")

        for index, district in enumerate(TARGET_DISTRICTS, 1):
            print(f"\n[{index}/{len(TARGET_DISTRICTS)}] Procesando: {district}")
            try:
                street_graph = dao.extract_graph(district)
                dao.save_graph(street_graph)
                
                successful_districts += 1
                time.sleep(2) 
                
            except Exception as e:
                print(f" ERROR processing '{district}': {e}")
                failed_districts.append(district)
                db.rollback() 
                continue
        
        print("--- Ingesta de red vial completada exitosamente ---")
        print(f"Resumen: {successful_districts} exitosos, {len(failed_districts)} fallidos.")
        
    except Exception as e:
        db.rollback()
        print(f"Ocurrió un error durante el proceso de ingestión: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run_street_network_ingestion()