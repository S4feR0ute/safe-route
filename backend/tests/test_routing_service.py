import pytest
import networkx as nx

from app.interfaces.street_graph_interface import IStreetGraphDAO
from app.interfaces.risk_score_interface import IRiskScoreRepository
from app.services.routing_service import RoutingService


class FakeStreetGraphDAO(IStreetGraphDAO):
    """DAO falso que devuelve un grafo sintetico en vez de consultar la BD real."""

    def __init__(self, graph: nx.MultiDiGraph):
        self._graph = graph

    def extract_graph(self, place_name: str) -> nx.MultiDiGraph:
        raise NotImplementedError("No se usa en este test")

    def save_graph(self, graph: nx.MultiDiGraph, place_name: str) -> int:
        raise NotImplementedError("No se usa en este test")

    def load_graph(self) -> nx.MultiDiGraph:
        return self._graph


class FakeRiskScoreRepository(IRiskScoreRepository):
    """Repositorio falso de scores: devuelve scores sinteticos sin tocar la BD."""

    def __init__(self, scores: dict):
        self._scores = scores

    def get_scores_by_edge(self, segment_id):
        return None

    def get_all_scores_as_dict(self):
        return {}

    def save_score(self, *args, **kwargs):
        pass

    def get_scores_mapped_by_nodes(self):
        return self._scores

    def bulk_save_scores(self, scores_data):
        return 0


def construir_grafo_sintetico() -> nx.MultiDiGraph:
    """
    4 nodos: 1 (origen) y 4 (destino), con 2 y 3 como camino alternativo.

      1 --------- 1000m, riesgo 0.90 ---------> 4
      1 -400m,0.10-> 2 -400m,0.10-> 3 -400m,0.10-> 4
    """
    graph = nx.MultiDiGraph()
    graph.add_node(1, x=0, y=0)
    graph.add_node(2, x=0.005, y=0)
    graph.add_node(3, x=0.005, y=0.003)
    graph.add_node(4, x=0, y=0.005)

    aristas = [
        (1, 4, 1000.0, "Via Directa Riesgosa"),
        (1, 2, 400.0, "Tramo Seguro 1"),
        (2, 3, 400.0, "Tramo Seguro 2"),
        (3, 4, 400.0, "Tramo Seguro 3"),
    ]
    for u, v, length, nombre in aristas:
        graph.add_edge(
            u, v,
            length=length,
            name=nombre,
            highway="residential",
            oneway=False,
            geometry=None,
        )
    return graph


@pytest.fixture
def scores_sinteticos():
    """composite_score por arista (u, v): 0.90 = muy riesgosa, 0.10 = muy segura."""
    return {(1, 4): 0.90, (1, 2): 0.10, (2, 3): 0.10, (3, 4): 0.10}


@pytest.fixture
def routing_service(monkeypatch, scores_sinteticos):
    grafo = construir_grafo_sintetico()
    fake_dao = FakeStreetGraphDAO(grafo)
    fake_score_repo = FakeRiskScoreRepository(scores_sinteticos)

    monkeypatch.setattr(
        RoutingService, "_cargar_scores_por_arista", lambda self: scores_sinteticos
    )

    return RoutingService(db=None, graph_dao=fake_dao, score_repo=fake_score_repo)


def test_ruta_segura_prefiere_camino_largo_pero_seguro(routing_service):
    resultado = routing_service.calcular_rutas(
        origen_lat=0, origen_lon=0, destino_lat=0.005, destino_lon=0
    )
    ruta_segura = resultado["ruta_segura"]

    assert ruta_segura["nodos"] == [1, 2, 3, 4]
    assert ruta_segura["longitud_total_m"] == pytest.approx(1200.0)
    assert ruta_segura["security_score"] == 90
    assert ruta_segura["categoria"] == "Segura"


def test_ruta_corta_prefiere_camino_directo_pero_riesgoso(routing_service):
    resultado = routing_service.calcular_rutas(
        origen_lat=0, origen_lon=0, destino_lat=0.005, destino_lon=0
    )
    ruta_corta = resultado["ruta_corta"]

    assert ruta_corta["nodos"] == [1, 4]
    assert ruta_corta["longitud_total_m"] == pytest.approx(1000.0)
    assert ruta_corta["security_score"] == 10
    assert ruta_corta["categoria"] == "Riesgosa"
