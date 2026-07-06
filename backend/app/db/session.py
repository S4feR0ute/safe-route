from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    Generador de sesiones para ser usado en los scripts o FastAPI.
    Asegura que la sesión se cierre después de usarse.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
