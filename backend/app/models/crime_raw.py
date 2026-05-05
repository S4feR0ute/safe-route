from sqlalchemy import Column, Integer, String, Float
from app.db.base import Base

class CrimeRawData(Base):
    __tablename__ = "crimen_raw_data"

    id = Column(Integer, primary_key=True, index=True)
    district_ubigeo = Column(String(10), index=True)
    district_name = Column(String)
    period = Column(String(4))
    crime_type = Column(String)
    incident_count = Column(Integer, default=0)