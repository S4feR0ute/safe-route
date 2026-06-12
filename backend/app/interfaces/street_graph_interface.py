import networkx as nx
from abc import ABC, abstractmethod


class IStreetGraphDAO(ABC):
    @abstractmethod
    def extract_graph(self, place_name: str) -> nx.MultiDiGraph:
        """Extrae un grafo vial desde OpenStreetMap."""
        pass

    @abstractmethod
    def save_graph(self, graph: nx.MultiDiGraph, place_name: str) -> int:
        """Guarda nodos y segmentos en PostgreSQL/PostGIS. Retorna cuántos segmentos insertó."""
        pass

    @abstractmethod
    def load_graph(self) -> nx.MultiDiGraph:
        """Reconstruye el grafo desde la base de datos."""
        pass
