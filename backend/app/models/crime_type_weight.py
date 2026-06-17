from sqlalchemy import Column, Integer, String, Float, Boolean
from app.db.base import Base


class CrimeTypeWeight(Base):
    """
    Tabla de pesos por tipo de delito.
    Permite ajustar la ponderación sin tocar el código fuente.
    """
    __tablename__ = "crime_types_weights"

    id = Column(Integer, primary_key=True, index=True)
    subtype_name = Column(String, unique=True, index=True)
    danger_weight = Column(Float, default=1.0)
    # is_street_crime: filtra delitos que ocurren en la vía pública
    is_street_crime = Column(Boolean, default=True)
