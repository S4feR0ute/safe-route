from abc import ABC, abstractmethod

import pandas as pd
from sqlalchemy.orm import Session


class ScoreLayer(ABC):
    def __init__(self, db: Session):
        self.db = db

    @abstractmethod
    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        """Añade la columna de score de esta capa al DataFrame y lo devuelve."""
        raise NotImplementedError
