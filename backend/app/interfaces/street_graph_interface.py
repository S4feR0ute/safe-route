import osmnx as ox
import networkx as nx
from abc import ABC, abstractmethod


class IStreetGraphDAO(ABC):
    @abstractmethod
    def extract_graph(self, city_name: str) -> nx.MultiDiGraph:
        """Extrae un grafo vial desde OpenStreetMap."""
        pass

    @abstractmethod
    def save_graph(self, graph: nx.MultiDiGraph, filepath: str) -> None:
        """Persiste el grafo para su uso posterior."""
        pass

    @abstractmethod
    def load_graph(self, filepath: str) -> nx.MultiDiGraph:
        """Carga un grafo previamente almacenado."""
        pass