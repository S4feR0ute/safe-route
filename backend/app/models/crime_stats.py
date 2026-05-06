from sqlalchemy import Column, Integer, String, Float
from app.db.base import Base

class DistrictCrimeStats(Base):
    __tablename__ = "district_crime_stats"

    id = Column(Integer, primary_key=True, index=True)
    district_ubigeo = Column(String(10), unique=True, index=True)
    district_name = Column(String)
    total_incidents_count = Column(Integer)
    weighted_crime_rate = Column(Float)