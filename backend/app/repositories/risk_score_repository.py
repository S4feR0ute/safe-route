from typing import Dict
from sqlalchemy.orm import Session
from app.models.risk_score import RiskScore
from app.models.street_network import StreetSegment


class RiskScoreRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_scores_mapped_by_nodes(self) -> Dict[tuple, float]:
        """Retorna un diccionario: {(source_node, target_node) -> composite_score}."""
        segments = self.db.query(
            StreetSegment.source_node_id,
            StreetSegment.target_node_id,
            RiskScore.composite_score
        ).join(
            RiskScore, StreetSegment.id == RiskScore.segment_id
        ).filter(
            RiskScore.composite_score.isnot(None)
        ).all()

        return {(src, tgt): score for src, tgt, score in segments}

    def save_score(
            self,
            segment_id: int,
            district_score: float,
            context_score: float,
            composite_score: float
        ) -> RiskScore:
        """Crea o actualiza el score para un segmento."""
        existing = self.db.query(RiskScore).filter(
            RiskScore.segment_id == segment_id
        ).first()

        if existing:
            existing.district_score = district_score
            existing.context_score = context_score
            existing.composite_score = composite_score
        else:
            existing = RiskScore(
                segment_id=segment_id,
                district_score=district_score,
                context_score=context_score,
                composite_score=composite_score,
            )
            self.db.add(existing)

        return existing
