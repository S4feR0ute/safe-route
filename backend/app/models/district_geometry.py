# app/models/district_geometry.py

from sqlalchemy import Column, String, Text
from geoalchemy2 import Geometry
from app.db.base import Base

class DistrictGeometry(Base):
    """Modelo para geometrías de distritos de Lima y Callao.
    
    Contiene polígonos de cada distrito para operaciones espaciales como
    ST_Within (asignar segmentos a distritos).
    """
    __tablename__ = "districts"

    ubigeo = Column(String(10), primary_key=True, index=True)
    district_name = Column(String(100), nullable=False)
    geometry = Column(
        Geometry(geometry_type='MULTIPOLYGON', srid=4326, spatial_index=True),
        nullable=False
    )