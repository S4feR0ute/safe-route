import logging
import time

import pandas as pd
from sqlalchemy import text, bindparam

from app.core.constants import (
    NEUTRAL_SCORE,
    CONTEXT_WEIGHT_LIGHTING, CONTEXT_WEIGHT_POLICE,
    CONTEXT_WEIGHT_ROAD_TYPE, CONTEXT_WEIGHT_CAMERAS, CONTEXT_WEIGHT_COMMERCE,
    HIGHWAY_RISK, HIGHWAY_RISK_DEFAULT,
)
from app.services.scoring.base import ScoreLayer

logger = logging.getLogger(__name__)

# Radio de influencia (metros) por tipo de POI para el context_score
POI_RADII_M = {
    "surveillance_camera": 150,
    "bank": 150,
    "street_lamp": 50,
    "shop": 100,
    "restaurant": 100,
    "pharmacy": 100,
    "fuel": 100,
    "marketplace": 100,
}
COMMERCE_POI_TYPES = ("shop", "restaurant", "pharmacy", "fuel", "marketplace")


class ContextScoreLayer(ScoreLayer):
    """Capa 2: score de contexto urbano (iluminación, policía, vía, vigilancia, comercio)."""

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        # Tipo de vía
        df["r_road"] = df["highway_type"].map(HIGHWAY_RISK).fillna(HIGHWAY_RISK_DEFAULT)
        df["has_road"] = True

        # Presencia policial
        logger.info("Consultando distancias a comisarías (ST_DWithin 700m)...")
        start = time.monotonic()
        df_police = self._query_police_distance()
        logger.info(f"  listo en {time.monotonic() - start:.0f}s")
        df = df.merge(df_police, on="id", how="left")
        df["police_dist"] = df["police_dist"].fillna(9999.0)
        df["r_police"] = df["police_dist"].apply(self._police_factor)
        df["has_police"] = df["police_dist"] < 700  # Tiene dato si está dentro del radio

        # Conteo de POIs por tipo en una sola query
        logger.info("Contando POIs cercanos por tipo (una sola query espacial)...")
        start = time.monotonic()
        counts = self._query_all_poi_counts()
        logger.info(f"  listo en {time.monotonic() - start:.0f}s")

        def poi_count(poi_type: str) -> pd.Series:
            if poi_type in counts.columns:
                return df["id"].map(counts[poi_type]).fillna(0)
            return pd.Series(0.0, index=df.index)

        # Vigilancia: cámaras (150m) + bancos (150m) contribuyen a seguridad
        camera_count = poi_count("surveillance_camera")
        df["has_cameras"] = camera_count > 0
        df["r_cameras"] = (1 - ((camera_count + poi_count("bank")) / 2).clip(0, 1))

        # Iluminación: postes de luz (50m), normalizamos por 5 lámparas
        lighting_count = poi_count("street_lamp")
        df["r_lighting"] = (1 - (lighting_count / 5).clip(0, 1))
        df["has_lighting"] = lighting_count > 0

        # Comercio (100m): esperamos ~10 POIs de actividad comercial
        commerce_count = sum(poi_count(t) for t in COMMERCE_POI_TYPES)
        df["r_commerce"] = (1 - (commerce_count / 10).clip(0, 1))
        df["has_commerce"] = commerce_count > 0

        # --- Combinar factores con pesos redistribuidos ---
        def compute_row_context_score(row):
            factors = [
                ("lighting", row["r_lighting"], CONTEXT_WEIGHT_LIGHTING, row["has_lighting"]),
                ("police", row["r_police"], CONTEXT_WEIGHT_POLICE, row["has_police"]),
                ("road", row["r_road"], CONTEXT_WEIGHT_ROAD_TYPE, row["has_road"]),
                ("cameras", row["r_cameras"], CONTEXT_WEIGHT_CAMERAS, row["has_cameras"]),
                ("commerce", row["r_commerce"], CONTEXT_WEIGHT_COMMERCE, row["has_commerce"]),
            ]

            # Suma de pesos para factores con datos
            active_weight = sum(weight for _, _, weight, has_data in factors if has_data)

            # Si no hay factores con datos, devolver NEUTRAL_SCORE
            if active_weight == 0:
                return NEUTRAL_SCORE

            # Sumar valor × peso redistribuido
            return sum(
                value * (weight / active_weight)
                for _, value, weight, has_data in factors
                if has_data
            )

        df["context_score"] = df.apply(compute_row_context_score, axis=1).clip(0.0, 1.0).round(4)

        # Limpiar columnas temporales
        df.drop(columns=["has_lighting", "has_police", "has_road", "has_cameras", "has_commerce"], inplace=True)

        return df

    def _police_factor(self, distance_m: float) -> float:
        """Convierte distancia a comisaría en riesgo (SAF-16, factor 2)."""
        if distance_m <= 300:
            return 0.0   # p_police = 1.0 -> r = 0
        elif distance_m <= 600:
            return 0.5   # p_police = 0.5 -> r = 0.5
        else:
            return 1.0   # p_police = 0.0 -> r = 1.0

    def _query_police_distance(self) -> pd.DataFrame:
        sql = text("""
            SELECT
                s.id,
                MIN(ST_Distance(
                    s.geometry::geography,
                    p.geometry::geography
                )) AS police_dist
            FROM street_segments s
            LEFT JOIN urban_pois p
                ON p.poi_type = 'police_station'
                AND ST_DWithin(
                    s.geometry::geography,
                    p.geometry::geography,
                    700
                )
            GROUP BY s.id
        """)
        rows = self.db.execute(sql).fetchall()
        return pd.DataFrame(rows, columns=["id", "police_dist"])

    def _query_all_poi_counts(self) -> pd.DataFrame:
        """
        Cuenta POIs cercanos a cada segmento, por tipo, en una sola pasada
        espacial (antes eran 8 queries separadas). El radio depende del tipo
        (POI_RADII_M). Devuelve un DataFrame pivotado: índice = segment id,
        una columna por poi_type; los segmentos sin POIs cercanos no aparecen
        (el caller asume 0).
        """
        radius_case = " ".join(
            f"WHEN '{poi_type}' THEN {radius}"
            for poi_type, radius in POI_RADII_M.items()
        )
        sql = text(f"""
            SELECT
                s.id,
                p.poi_type,
                COUNT(p.id) AS poi_count
            FROM street_segments s
            JOIN urban_pois p
                ON p.poi_type IN :poi_types
                AND ST_DWithin(
                    s.geometry::geography,
                    p.geometry::geography,
                    CASE p.poi_type {radius_case} END
                )
            GROUP BY s.id, p.poi_type
        """).bindparams(bindparam("poi_types", expanding=True))
        rows = self.db.execute(
            sql, {"poi_types": list(POI_RADII_M.keys())}
        ).fetchall()

        df = pd.DataFrame(rows, columns=["id", "poi_type", "poi_count"])
        if df.empty:
            return df
        return df.pivot(index="id", columns="poi_type", values="poi_count").fillna(0)
