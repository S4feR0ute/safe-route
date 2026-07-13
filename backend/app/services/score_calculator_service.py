import logging
import time
from datetime import datetime

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.risk_score import RiskScore
from app.core.constants import WEIGHT_DISTRICT, WEIGHT_CONTEXT, WEIGHT_REPORT
from app.services.scoring import (
    DistrictScoreLayer,
    ContextScoreLayer,
    ReportScoreLayer,
)

logger = logging.getLogger(__name__)


class ScoreCalculatorService:
    """
    Orquesta el cálculo del composite_score de cada segmento aplicando, en orden,
    las capas de scoring (distrito, contexto, reportes) y combinándolas.
    """

    def __init__(self, db: Session):
        self.db = db
        self.layers = [
            DistrictScoreLayer(db),
            ContextScoreLayer(db),
            ReportScoreLayer(db),
        ]

    def calculate_all_scores(self) -> int:
        logger.info("Cargando segmentos de la BD")
        df = self._load_segments()

        if df.empty:
            logger.warning("No hay segmentos en la BD")
            return 0

        logger.info(f"{len(df)} segmentos encontrados")

        # Aplicar cada capa de scoring 
        for layer in self.layers:
            name = type(layer).__name__
            logger.info(f"Aplicando {name}")
            start = time.monotonic()
            df = layer.apply(df)
            logger.info(f"  {name} listo en {time.monotonic() - start:.0f}s")

        # Fórmula compuesta
        base = (WEIGHT_DISTRICT * df["district_score"] + WEIGHT_CONTEXT * df["context_score"])
        df["composite_score"] = np.where(
            df["report_score"] > 0,
            (1 - WEIGHT_REPORT) * base + WEIGHT_REPORT * df["report_score"],
            base,
        )
        df["composite_score"] = df["composite_score"].clip(0.0, 1.0).round(4)

        #Guardar en risk_scores
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
