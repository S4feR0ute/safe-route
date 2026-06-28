from abc import ABC, abstractmethod
from typing import Dict, Optional
from app.models.risk_score import RiskScore


class IRiskScoreRepository(ABC):
    @abstractmethod
    def get_scores_by_edge(self, segment_id: int) -> Optional[RiskScore]:
        """Obtiene el score compuesto para un segmento específico."""
        pass

    @abstractmethod
    def get_all_scores_as_dict(self) -> Dict[int, float]:
        """Retorna un diccionario: {segment_id -> composite_score}"""
        pass

    @abstractmethod
    def save_score(self, segment_id: int, district_score: float, context_score: float, composite_score: float) -> RiskScore:
        """Crea o actualiza el score para un segmento."""
        pass

    @abstractmethod
    def bulk_save_scores(self, scores_data: list) -> int:
        """Inserta/actualiza múltiples scores de una vez."""
        pass
