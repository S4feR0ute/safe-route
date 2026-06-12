from sqlalchemy import Column, Integer, BigInteger, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from app.db.base import Base

class StreetNode(Base):
    __tablename__ = "street_nodes"

    node_id = Column(BigInteger, primary_key=True, index=True)
    geometry = Column(Geometry(geometry_type='POINT', srid=4326, spatial_index=True))
    lat = Column(Float)
    lon = Column(Float)


class StreetSegment(Base):
    __tablename__ = "street_segments"

    id = Column(Integer, primary_key=True, index=True)
    osm_way_id = Column(BigInteger, index=True)
    geometry = Column(Geometry(geometry_type='LINESTRING', srid=4326, spatial_index=True))
    name = Column(String, nullable=True)
    length_m = Column(Float)
    highway_type = Column(String)
    oneway = Column(Boolean, default=False)
    source_node_id = Column(BigInteger, ForeignKey('street_nodes.node_id', ondelete="CASCADE"), index=True)
    target_node_id = Column(BigInteger, ForeignKey('street_nodes.node_id', ondelete="CASCADE"), index=True) 
    district_ubigeo = Column(String(10), index=True, nullable=True)