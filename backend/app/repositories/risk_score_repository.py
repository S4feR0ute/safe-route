from typing import Dict, Optional, Tuple
from app.interfaces.risk_score_interface import IRiskScoreRepository
from sqlalchemy.orm import Session
from app.models.risk_score import RiskScore


class RiskScoreRepository(IRiskScoreRepository):
    """
    Repository para acceder a los scores de riesgo.
    Abstrae las queries a la tabla risk_scores.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_scores_by_edge(self, segment_id: int) -> Optional[RiskScore]:
        """Obtiene el score compuesto para un segmento específico."""
        return self.db.query(RiskScore).filter(
            RiskScore.segment_id == segment_id
        ).first()

    def get_all_scores_as_dict(self) -> Dict[int, float]:
        """
        Retorna un diccionario: {segment_id -> composite_score}
        Optimizado para cargar todos los scores de una vez.
        """
        scores = self.db.query(
            RiskScore.segment_id,
            RiskScore.composite_score
        ).all()
        return {segment_id: score for segment_id, score in scores}

    def get_scores_mapped_by_nodes(self) -> Dict[tuple, float]:
        """
        Retorna un diccionario: {(source_node, target_node) -> composite_score}
        Para uso en RoutingService.
        """
        from app.models.street_network import StreetSegment
        from sqlalchemy.orm import joinedload

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

    def save_score(self, segment_id: int, district_score: float, context_score: float, composite_score: float) -> RiskScore:
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

    def bulk_save_scores(self, scores_data: list) -> int:
        """
        Inserta/actualiza múltiples scores de una vez.
        scores_data: List[{segment_id, district_score, context_score, composite_score}]
        Retorna cantidad de registros procesados.
        """
        count = 0
        for data in scores_data:
            self.save_score(**data)
            count += 1
        return count
