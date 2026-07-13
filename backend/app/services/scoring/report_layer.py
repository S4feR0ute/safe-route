import logging
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from sqlalchemy import text

from app.core.constants import (
    REPORT_INFLUENCE_RADIUS_M, REPORT_HALF_LIFE_DAYS, REPORT_MAX_AGE_DAYS,
    REPORT_SATURATION, REPORT_TYPE_WEIGHTS, REPORT_TYPE_WEIGHT_DEFAULT,
    REPORT_SEVERITY_FACTOR, REPORT_SEVERITY_FACTOR_DEFAULT,
)
from app.services.scoring.base import ScoreLayer

logger = logging.getLogger(__name__)


class ReportScoreLayer(ScoreLayer):
    """Capa 3: aporte de reportes ciudadanos validados cercanos a cada segmento."""

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        # Consulta los reportes validados cercanos a cada segmento y calcula su aporte al score.
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
