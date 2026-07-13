import logging
import osmnx as ox
import geopandas as gpd
from sqlalchemy.orm import Session
from app.models.urban_context import UrbanPOI
from app.utils.osm_helpers import setup_osmnx, normalize_tag_value, make_point_geometry

logger = logging.getLogger(__name__)


class OSMnxContextDAO:
    def __init__(self, db: Session):
        self.db = db
        setup_osmnx()

    def extract_pois(self, place_name: str, tags: dict) -> gpd.GeoDataFrame:
        """Extrae POIs de OSM para un lugar dado y un conjunto de tags."""
        logger.info(f"Buscando POIs en {place_name} con tags {tags}...")
        try:
            gdf = ox.features_from_place(place_name, tags=tags)
            logger.info(f"  -> {len(gdf)} resultados")
            return gdf
        except Exception as error:
            logger.warning(f"  -> Sin datos para {place_name}: {error}")
            return gpd.GeoDataFrame()

    def save_pois(self, gdf: gpd.GeoDataFrame, poi_type: str) -> int:
        """Guarda POIs en la base de datos, evitando duplicados por OSM ID."""
        if gdf.empty:
            logger.info(f"  -> No hay {poi_type} para guardar")
            return 0

        saved = 0
        for idx, row in gdf.iterrows():
            osm_id = str(idx[1]) if isinstance(idx, tuple) else str(idx)
            full_id = f"{poi_type}_{osm_id}"

            already_exists = self.db.query(UrbanPOI).filter(UrbanPOI.osm_id == full_id).first()
            
            if already_exists:
                continue

            geom = row.geometry
            if geom is None or geom.is_empty:
                continue
            if geom.geom_type != "Point":
                geom = geom.centroid

            poi = UrbanPOI(
                osm_id=full_id,
                poi_type=poi_type,
                name=normalize_tag_value(row.get("name"), default="Sin nombre"),
                geometry=make_point_geometry(geom.x, geom.y),
            )
            self.db.add(poi)
            saved += 1

        self.db.commit()
        logger.info(f"  -> {saved} POIs de tipo '{poi_type}' guardados")
        return saved
