from sqlalchemy import Column, Integer, BigInteger, String
from geoalchemy2 import Geometry
from app.db.base import Base


class UrbanPOI(Base):
    __tablename__ = "urban_pois"

    id = Column(Integer, primary_key=True, index=True)
    osm_id = Column(String, unique=True, index=True)
    poi_type = Column(String, index=True)
    name = Column(String, nullable=True)
    geometry = Column(Geometry(geometry_type='POINT', srid=4326, spatial_index=True))
