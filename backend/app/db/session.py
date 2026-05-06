from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL_LOCAL")

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