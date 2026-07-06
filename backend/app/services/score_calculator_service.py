import logging
import time
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import text, bindparam
from datetime import datetime, timedelta

from app.models.risk_score import RiskScore
from app.core.constants import (
    WEIGHT_DISTRICT, WEIGHT_CONTEXT, WEIGHT_REPORT,
    NEUTRAL_SCORE,
    CONTEXT_WEIGHT_LIGHTING, CONTEXT_WEIGHT_POLICE,
    CONTEXT_WEIGHT_ROAD_TYPE, CONTEXT_WEIGHT_CAMERAS, CONTEXT_WEIGHT_COMMERCE,
    HIGHWAY_RISK, HIGHWAY_RISK_DEFAULT,
    REPORT_INFLUENCE_RADIUS_M, REPORT_HALF_LIFE_DAYS, REPORT_MAX_AGE_DAYS,
    REPORT_SATURATION, REPORT_TYPE_WEIGHTS, REPORT_TYPE_WEIGHT_DEFAULT,
    REPORT_SEVERITY_FACTOR, REPORT_SEVERITY_FACTOR_DEFAULT,
)

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


class ScoreCalculatorService:
    """Calcula el score compuesto de riesgo para cada segmento de calle"""

    def __init__(self, db: Session):
        self.db = db

    def calculate_all_scores(self) -> int:
        logger.info("Cargando segmentos de la BD")
        df = self._load_segments()

        if df.empty:
            logger.warning("No hay segmentos en la BD")
            return 0

        logger.info(f"{len(df)} segmentos encontrados")

        # --- Capa 1: score distrital ---
        logger.info("Calculando district_score")
        df = self._add_district_score(df)

        # --- Capa 2: score de contexto urbano ---
        logger.info("Calculando context_score")
        df = self._add_context_score(df)

        # --- Capa 3: reportes ciudadanos validados ---
        logger.info("Calculando report_score (reportes validados, ST_DWithin 150m)")
        start = time.monotonic()
        df = self._add_report_score(df)
        logger.info(f"  listo en {time.monotonic() - start:.0f}s")

        # --- Fórmula compuesta ---
        base = (WEIGHT_DISTRICT * df["district_score"]+ WEIGHT_CONTEXT * df["context_score"])
        df["composite_score"] = np.where(
            df["report_score"] > 0,
            (1 - WEIGHT_REPORT) * base + WEIGHT_REPORT * df["report_score"],
            base,
        )
        df["composite_score"] = df["composite_score"].clip(0.0, 1.0).round(4)

        # --- Guardar en risk_scores ---
        logger.info("Guardando scores en la BD")
        self._save_scores(df)

        logger.info(f"{len(df)} scores guardados")
        return len(df)

    def _load_segments(self) -> pd.DataFrame:
        """Trae id, tipo de vía, ubigeo y longitud de todos los segmentos."""
        sql = text("""
            SELECT id, highway_type, district_ubigeo, length_m
            FROM street_segments
        """)
        rows = self.db.execute(sql).fetchall()
        return pd.DataFrame(rows, columns=["id", "highway_type", "district_ubigeo", "length_m"])

    def _add_district_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Hace un join con district_crime_stats para traer la tasa normalizada.
        Si el segmento no tiene ubigeo o el distrito no tiene datos, usa NEUTRAL_SCORE.
        """
        query = text("SELECT district_ubigeo, weighted_crime_rate FROM district_crime_stats")
        rows = self.db.execute(query).fetchall()
        df_rates = pd.DataFrame(rows, columns=["district_ubigeo", "weighted_crime_rate"])

        df = df.merge(df_rates, on="district_ubigeo", how="left")
        df["district_score"] = df["weighted_crime_rate"].fillna(NEUTRAL_SCORE)
        return df

    def _add_context_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula los factores y los combina con pesos redistribuidos.
        Si un factor no tiene datos (usa NEUTRAL_SCORE), su peso se redistribuye.
        """
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

    def _add_report_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Reportes ciudadanos con status='validated' dentro de
        REPORT_INFLUENCE_RADIUS_M de cada segmento. Cada reporte aporta
        min(peso_tipo * factor_severidad, 1.0) * 0.5^(edad_días/vida_media),
        la suma se normaliza por REPORT_SATURATION y se capea a 1.0.
        """
        now = datetime.utcnow()
        cutoff = now - timedelta(days=REPORT_MAX_AGE_DAYS)

        sql = text("""
            SELECT
                s.id AS segment_id,
                r.incident_type,
                r.severity_level,
                COALESCE(r.occurred_at, r.created_at) AS created_at
            FROM street_segments s
            JOIN incident_reports r
                ON r.status = 'validated'
                AND COALESCE(r.occurred_at, r.created_at) >= :cutoff
                AND ST_DWithin(
                    s.geometry::geography,
                    r.location::geography,
                    :radius
                )
        """)
        rows = self.db.execute(
            sql, {"cutoff": cutoff, "radius": REPORT_INFLUENCE_RADIUS_M}
        ).fetchall()

        if not rows:
            df["report_score"] = 0.0
            return df

        df_reports = pd.DataFrame(
            rows, columns=["segment_id", "incident_type", "severity_level", "created_at"]
        )

        type_weight = df_reports["incident_type"].map(REPORT_TYPE_WEIGHTS).fillna(
            REPORT_TYPE_WEIGHT_DEFAULT
        )
        severity_factor = df_reports["severity_level"].map(REPORT_SEVERITY_FACTOR).fillna(
            REPORT_SEVERITY_FACTOR_DEFAULT
        )
        age_days = (now - pd.to_datetime(df_reports["created_at"])).dt.total_seconds() / 86400.0
        decay = np.power(0.5, age_days / REPORT_HALF_LIFE_DAYS)

        df_reports["contribution"] = (type_weight * severity_factor).clip(upper=1.0) * decay

        per_segment = (
            df_reports.groupby("segment_id")["contribution"].sum() / REPORT_SATURATION
        ).clip(upper=1.0).rename("report_score").reset_index()
        per_segment.rename(columns={"segment_id": "id"}, inplace=True)

        df = df.merge(per_segment, on="id", how="left")
        df["report_score"] = df["report_score"].fillna(0.0).round(4)

        logger.info(
            f"{len(per_segment)} segmentos afectados por "
            f"{df_reports[['incident_type', 'created_at']].drop_duplicates().shape[0]} "
            f"reportes validados ({len(df_reports)} pares segmento-reporte)"
        )
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

    def _save_scores(self, df: pd.DataFrame):
        start = time.monotonic()
        self.db.query(RiskScore).delete()

        out = df[["id", "district_score", "context_score", "report_score", "composite_score"]].rename(
            columns={"id": "segment_id"}
        )
        out = out.astype({
            "segment_id": int,
            "district_score": float,
            "context_score": float,
            "report_score": float,
            "composite_score": float,
        })
        out["last_updated"] = datetime.utcnow()
        scores_data = out.to_dict("records")

        self.db.bulk_insert_mappings(RiskScore, scores_data)
        self.db.commit()
        logger.info(
            f"Insertados {len(scores_data)} scores vía bulk_insert "
            f"({time.monotonic() - start:.0f}s)"
        )
