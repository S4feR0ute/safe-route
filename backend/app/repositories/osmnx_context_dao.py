import osmnx as ox
import geopandas as gpd
from sqlalchemy.orm import Session
from app.interfaces.urban_context_interface import IUrbanContextDAO
from app.models.urban_context import UrbanPOI
from app.utils.osm_helpers import setup_osmnx, normalize_tag_value, make_point_geometry


class OSMnxContextDAO(IUrbanContextDAO):
    """DAO para extraer POIs de contexto urbano (comisarías, cámaras, etc.)."""

    def __init__(self, db_session: Session):
        self.db = db_session
        setup_osmnx()

    def extract_pois(self, place_name: str, tags: dict) -> gpd.GeoDataFrame:
        print(f"Buscando POIs en {place_name} con tags {tags}...")
        try:
            gdf = ox.features_from_place(place_name, tags=tags)
            print(f"  -> {len(gdf)} resultados")
            return gdf
        except Exception as error:
            print(f"  -> Sin datos para {place_name}: {error}")
            return gpd.GeoDataFrame()

    def save_pois(self, gdf: gpd.GeoDataFrame, poi_type: str) -> int:
        if gdf.empty:
            print(f"  -> No hay {poi_type} para guardar")
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
        print(f"  -> {saved} POIs de tipo '{poi_type}' guardados")
        return saved
