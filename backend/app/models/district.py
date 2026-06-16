from sqlalchemy import Column, Integer, String
from geoalchemy2 import Geometry
from app.db.base import Base


class District(Base):
    __tablename__ = "districts"

    id = Column(Integer, primary_key=True, index=True)
    ubigeo = Column(String(10), unique=True, index=True)
    name = Column(String)
    # Polígono del distrito en coordenadas WGS84
    geometry = Column(Geometry(geometry_type='POLYGON', srid=4326, spatial_index=True))
