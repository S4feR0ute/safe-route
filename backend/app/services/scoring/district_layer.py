import pandas as pd
from sqlalchemy import text

from app.core.constants import NEUTRAL_SCORE
from app.services.scoring.base import ScoreLayer


class DistrictScoreLayer(ScoreLayer):
    """Capa 1: score distrital a partir de la tasa de criminalidad normalizada."""

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        # Consulta la tabla de tasas de criminalidad por distrito y la une al DataFrame.
        query = text("SELECT district_ubigeo, weighted_crime_rate FROM district_crime_stats")
        rows = self.db.execute(query).fetchall()
        df_rates = pd.DataFrame(rows, columns=["district_ubigeo", "weighted_crime_rate"])

        df = df.merge(df_rates, on="district_ubigeo", how="left")
        df["district_score"] = df["weighted_crime_rate"].fillna(NEUTRAL_SCORE)
        return df
