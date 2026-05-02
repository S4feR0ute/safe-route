from sqlalchemy import Column, Integer, String, Float
from app.db.base import Base

class DistrictCrimeRate(Base):
    __tablename__ = "district_crime_rates"
    id = Column(Integer, primary_key=True)
    district_ubigeo = Column(String(10))
    district_name = Column(String)
    period = Column(String(4))
    crime_type = Column(String)
    incident_count = Column(Integer, default=0)