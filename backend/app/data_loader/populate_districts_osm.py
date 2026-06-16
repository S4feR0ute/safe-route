"""
Script para extraer geometrías de distritos desde OSM y guardarlas en BD.
Utiliza la lista exacta de TARGET_DISTRICTS para garantizar polígonos precisos.
"""

import sys
import time
from pathlib import Path
import osmnx as ox
from shapely.geometry import Polygon, MultiPolygon

# Permite ejecutar el script directamente sin instalar el paquete
BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.constants import TARGET_DISTRICTS
from app.db.session import SessionLocal
from app.models.district_geometry import DistrictGeometry
from app.utils.osm_helpers import setup_osmnx

# Mapeo actualizado con UBIGEOs oficiales y únicos del INEI
DISTRICT_UBIGEO_MAP = {
    # Lima
    "Lima": "150101",
    "Ancón": "150102",
    "Ate": "150103",
    "Barranco": "150104",
    "Breña": "150105",
    "Carabayllo": "150106",
    "Chaclacayo": "150107",
    "Chorrillos": "150108",
    "Cieneguilla": "150109",
    "Comas": "150110",
    "El Agustino": "150111",
    "Independencia": "150112",
    "Jesús María": "150113",
    "La Molina": "150114",
    "La Victoria": "150115",
    "Lince": "150116",
    "Los Olivos": "150117",
    "Lurigancho": "150118",
    "Lurín": "150119",
    "Magdalena del Mar": "150120",
    "Pueblo Libre": "150121",
    "Miraflores": "150122",
    "Pachacámac": "150123",
    "Pucusana": "150124",
    "Puente Piedra": "150125",
    "Punta Hermosa": "150126",
    "Punta Negra": "150127",
    "Rímac": "150128",
    "San Bartolo": "150129",
    "San Borja": "150130",
    "San Isidro": "150131",
    "San Juan de Lurigancho": "150132",
    "San Juan de Miraflores": "150133",
    "San Luis": "150134",
    "San Martín de Porres": "150135",
    "San Miguel": "150136",
    "Santa Anita": "150137",
    "Santa María del Mar": "150138",
    "Santa Rosa": "150139",
    "Santiago de Surco": "150140",
    "Surquillo": "150141",
    "Villa El Salvador": "150142",
    "Villa María del Triunfo": "150143",
    
    # Callao
    "Callao": "070101",
    "Bellavista": "070102",
    "Carmen de la Legua Reynoso": "070103",
    "Carmen de La Legua-Reynoso": "070103",
    "La Perla": "070104",
    "La Punta": "070105",
    "Ventanilla": "070106",
    "Mi Perú": "070107",
}

def populate_districts_from_osm():
    db = SessionLocal()
    setup_osmnx()
    
    try:
        print(" Extracción de geometrías de distritos exacta desde OSM \n")
        
        # Limpiamos las filas, la estructura MULTIPOLYGON ya está bien en BD
        print("Limpiando tabla de distritos existentes...")
        db.query(DistrictGeometry).delete()
        db.commit()
        
        districts_to_save = []
        
        # Iteramos directamente sobre las consultas exactas que usa el script de ingesta
        for place_query in TARGET_DISTRICTS:
            print(f"Consultando polígono para: {place_query}")
            
            # Extraer el nombre base (ej: "Miraflores, Lima, Peru" -> "Miraflores")
            district_name = place_query.split(",")[0].strip()
            
            # Normalizar nombres que tienen "District"
            if district_name == "Lima District":
                district_name = "Lima"
            elif district_name == "Callao District":
                district_name = "Callao"
            
            ubigeo = DISTRICT_UBIGEO_MAP.get(district_name)
            if not ubigeo:
                print(f"  -> IGNORADO: '{district_name}' no está en el mapa UBIGEO.")
                continue
                
            try:
                # geocode_to_gdf obtiene el polígono exacto (sin ruido ni provincias)
                gdf = ox.geocode_to_gdf(place_query)
                
                if gdf.empty:
                    print(f"  -> ERROR: Sin polígono encontrado para {place_query}")
                    continue
                
                geometry = gdf.iloc[0]['geometry']
                
                # Estandarizar a MultiPolygon
                if isinstance(geometry, Polygon):
                    geometry = MultiPolygon([geometry])
                elif not isinstance(geometry, MultiPolygon):
                    print(f"  -> ERROR: Geometría inválida ({type(geometry)}) para {place_query}")
                    continue
                    
                district = DistrictGeometry(
                    ubigeo=ubigeo,
                    district_name=district_name,
                    geometry=f"SRID=4326;{geometry.wkt}"
                )
                districts_to_save.append(district)
                print(f"  -> OK: {district_name} ({ubigeo})")
                
                time.sleep(1) # Respetar límites de OSM
                
            except Exception as e:
                print(f"  -> ERROR crítico procesando {place_query}: {e}")
                continue
        
        if districts_to_save:
            print(f"\nGuardando {len(districts_to_save)} distritos exactos en BD...")
            db.add_all(districts_to_save)
            db.commit()
            print("✓ Proceso completado con éxito")
        
        count = db.query(DistrictGeometry).count()
        print(f"Total de distritos en BD: {count}")
        
    except Exception as e:
        db.rollback()
        print(f"Error general: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    populate_districts_from_osm()