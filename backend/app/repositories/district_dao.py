import logging
import osmnx as ox
from sqlalchemy.orm import Session
from geoalchemy2.elements import WKTElement
from app.core.constants import GEOCODE_QUERY_OVERRIDES
from app.interfaces.district_interface import IDistrictDAO
from app.models.district import District
from app.utils.osm_helpers import setup_osmnx

logger = logging.getLogger(__name__)


class OSMnxDistrictDAO(IDistrictDAO):
    """DAO para extraer y guardar los polígonos de los distritos usando OSMnx."""
    
    def __init__(self, db: Session):
        self.db = db
        setup_osmnx()

    def extract_boundary(self, place_name: str, ubigeo: str) -> dict | None:
        logger.info(f"Extrayendo polígono de: {place_name}")
        try:
            # Algunos nombres son ambiguos en texto libre para Nominatim; en esos casos se usa una query estructurada.
            query = GEOCODE_QUERY_OVERRIDES.get(place_name, place_name)

            # ox.geocode_to_gdf devuelve un GeoDataFrame con el polígono del lugar
            gdf = ox.geocode_to_gdf(query)

            if gdf.empty:
                logger.warning(f"Sin resultado para {place_name}")
                return None

            # Tomamos la primera geometría
            geom = gdf.iloc[0].geometry

            # Nos aseguramos de tener un polígono, no un multipolygon
            if geom.geom_type == "MultiPolygon":
                # Quedarse con el polígono más grande del multipolígono
                geom = max(geom.geoms, key=lambda p: p.area)

            if geom.geom_type != "Polygon":
                logger.warning(f"Geometría inesperada ({geom.geom_type}) para {place_name}")
                return None

            district_name = place_name.split(",")[0].strip()

            return {
                "ubigeo": ubigeo,
                "name": district_name,
                "geometry_wkt": geom.wkt,
            }

        except Exception as error:
            logger.error(f"Error extrayendo {place_name}: {error}")
            return None

    def save_boundary(self, boundary_data: dict) -> bool:
        ubigeo = boundary_data["ubigeo"]

        # Revisar si ya existe en la BD
        existing = self.db.query(District).filter(District.ubigeo == ubigeo).first()

        if existing:
            # Actualizar geometría si ya existe
            existing.geometry = WKTElement(boundary_data["geometry_wkt"], srid=4326)
            existing.name = boundary_data["name"]
            logger.info(f"Distrito '{boundary_data['name']}' actualizado")
            return False
        else:
            # Crear nuevo registro
            new_district = District(
                ubigeo=ubigeo,
                name=boundary_data["name"],
                geometry=WKTElement(boundary_data["geometry_wkt"], srid=4326),
            )
            self.db.add(new_district)
            logger.info(f"Distrito '{boundary_data['name']}' guardado")
            return True
