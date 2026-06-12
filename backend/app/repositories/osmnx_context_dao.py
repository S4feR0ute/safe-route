import osmnx as ox
import geopandas as gpd
from sqlalchemy.orm import Session
from app.interfaces.urban_context_interface import IUrbanContextDAO
from app.models.urban_context import UrbanPOI

class OSMnxContextDAO(IUrbanContextDAO):
    def __init__(self, db_session: Session):
        self.db = db_session
        ox.settings.use_cache = True
        ox.settings.log_console = True

    def extract_pois(self, place_name: str, tags: dict) -> gpd.GeoDataFrame:
        print(f"Extraer POIs para {place_name} con los tags: {tags}...")
        try:
            gdf = ox.features_from_place(place_name, tags=tags)
            return gdf
        except Exception as e:
            print(f"No features found or error for {place_name}: {e}")
            return gpd.GeoDataFrame()

    def save_pois_to_db(self, gdf: gpd.GeoDataFrame, poi_type: str) -> None:
        if gdf.empty:
            return

        pois_to_insert = []
        
        for idx, row in gdf.iterrows():
            osm_id = str(idx[1]) if isinstance(idx, tuple) else str(idx)
            
            # Obtener el nombre si existe
            name = row.get('name', 'Unknown')
            if isinstance(name, float): # Manejo de NaNs de Pandas
                name = 'Unknown'

            # Normalización geométrica:
            geom = row.geometry
            if geom.geom_type != 'Point':
                geom = geom.centroid

            lon, lat = geom.x, geom.y
            geom_wkt = f"SRID=4326;POINT({lon} {lat})"

            # Crear instancia del modelo
            poi = UrbanPOI(
                osm_id=f"{poi_type}_{osm_id}", # Prefijo para evitar colisiones de IDs de OSM
                poi_type=poi_type,
                name=str(name),
                geometry=geom_wkt
            )
            pois_to_insert.append(poi)

        for poi in pois_to_insert:
            exists = self.db.query(UrbanPOI).filter(UrbanPOI.osm_id == poi.osm_id).first()
            if not exists:
                self.db.add(poi)
                
        self.db.commit()
        print(f"Guardar {len(pois_to_insert)} {poi_type} POIs en la base de datos.")