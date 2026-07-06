import pytest
from fastapi.testclient import TestClient

from api_app import app
from app.db.session import get_db
from app.core.service_container import ServiceContainer
from app.core.exceptions import EmptyGraphError, NoRouteError
from app.services.routing_service import RoutingService


def fake_get_db():
    yield None


app.dependency_overrides[get_db] = fake_get_db


class FakeRoutingServiceOK(RoutingService):
    """Simula una respuesta exitosa del RoutingService, sin tocar la BD ni OSMnx.

    Hereda de RoutingService para reutilizar build_route_response real.
    """

    def __init__(self):
        super().__init__(db=None, graph_dao=None, score_repo=None)

    def calculate_routes(self, **kwargs):
        safe_segment = {
            "source_node": 1, "target_node": 2, "name": "Calle Test",
            "length_m": 1200.0, "composite_score": 0.10,
            "coordinates": [[0, 0], [0, 0.005]],
        }
        short_segment = {
            "source_node": 1, "target_node": 4, "name": "Calle Test Corta",
            "length_m": 1000.0, "composite_score": 0.90,
            "coordinates": [[0, 0], [0, 0.005]],
        }
        return {
            "safe_route": {
                "nodes": [1, 2, 3, 4], "segments": [safe_segment],
                "total_length_m": 1200.0, "security_score": 90, "category": "Segura",
            },
            "short_route": {
                "nodes": [1, 4], "segments": [short_segment],
                "total_length_m": 1000.0, "security_score": 10, "category": "Riesgosa",
            },
        }


def make_failing_service(excepcion):
    """Crea una version falsa del RoutingService que siempre lanza la excepcion dada."""
    class FakeRoutingServiceFail(FakeRoutingServiceOK):
        def calculate_routes(self, **kwargs):
            raise excepcion
    return FakeRoutingServiceFail


def use_routing_service(monkeypatch, service_cls):
    """Hace que el contenedor DI devuelva el servicio falso."""
    monkeypatch.setattr(
        ServiceContainer, "get_routing_service", lambda self: service_cls()
    )


@pytest.fixture
def client():
    return TestClient(app)


ORIGEN = {"lat": -12.046, "lon": -77.043}
DESTINO = {"lat": -12.056, "lon": -77.033}


def test_origen_igual_a_destino_retorna_400(client):
    body = {"origin": ORIGEN, "destination": {"lat": ORIGEN["lat"] + 0.0001, "lon": ORIGEN["lon"]}}
    resp = client.post("/api/v1/route", json=body)
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


def test_distancia_excede_maximo_retorna_400(client):
    body = {"origin": {"lat": -12.0, "lon": -77.0}, "destination": {"lat": -12.3, "lon": -77.0}}
    resp = client.post("/api/v1/route", json=body)
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


def test_payload_invalido_retorna_422(client):
    body = {"origin": ORIGEN}  # falta "destination"
    resp = client.post("/api/v1/route", json=body)
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


def test_ruta_valida_retorna_200_con_estructura_esperada(client, monkeypatch):
    use_routing_service(monkeypatch, FakeRoutingServiceOK)

    body = {"origin": ORIGEN, "destination": DESTINO}
    resp = client.post("/api/v1/route", json=body)

    app.dependency_overrides.pop(get_service_container, None)

    assert resp.status_code == 200
    data = resp.json()
    assert data["safe_route"]["summary"]["security_score"] == 90
    assert data["safe_route"]["summary"]["category"] == "Segura"
    assert data["shortest_route"]["summary"]["security_score"] == 10
    assert data["comparison"] is not None
    assert len(data["safe_route"]["geojson"]["features"]) == 1


def test_include_shortest_false_omite_ruta_corta_y_comparacion(client, monkeypatch):
    use_routing_service(monkeypatch, FakeRoutingServiceOK)

    body = {"origin": ORIGEN, "destination": DESTINO, "include_shortest": False}
    resp = client.post("/api/v1/route", json=body)

    app.dependency_overrides.pop(get_service_container, None)

    assert resp.status_code == 200
    data = resp.json()
    assert data["shortest_route"] is None
    assert data["comparison"] is None


def test_no_existe_ruta_retorna_404(client, monkeypatch):
    fake = make_failing_service(NoRouteError("No existe ruta entre los puntos seleccionados"))
    use_routing_service(monkeypatch, fake)

    resp = client.post("/api/v1/route", json={"origin": ORIGEN, "destination": DESTINO})

    app.dependency_overrides.pop(get_service_container, None)

    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "NOT_FOUND"


def test_grafo_vacio_retorna_503(client, monkeypatch):
    fake = make_failing_service(EmptyGraphError("El grafo está vacío"))
    use_routing_service(monkeypatch, fake)

    resp = client.post("/api/v1/route", json={"origin": ORIGEN, "destination": DESTINO})

    app.dependency_overrides.pop(get_service_container, None)

    assert resp.status_code == 503


def test_error_inesperado_retorna_500(client, monkeypatch):
    fake = make_failing_service(RuntimeError("boom"))
    use_routing_service(monkeypatch, fake)

    resp = client.post("/api/v1/route", json={"origin": ORIGEN, "destination": DESTINO})

    app.dependency_overrides.pop(get_service_container, None)

    assert resp.status_code == 500
