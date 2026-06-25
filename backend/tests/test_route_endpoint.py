import pytest
from fastapi.testclient import TestClient

from api_app import app
from app.db.session import get_db
import app.api.route_endpoint as route_endpoint


def fake_get_db():
    """Sustituye la conexion real a la BD: para estos tests no se necesita."""
    yield None


app.dependency_overrides[get_db] = fake_get_db


class FakeRoutingServiceOK:
    """Simula una respuesta exitosa del RoutingService, sin tocar la BD ni OSMnx."""

    def __init__(self, db=None, graph_dao=None):
        pass

    def calcular_rutas(self, **kwargs):
        segmento_segura = {
            "source_node": 1, "target_node": 2, "name": "Calle Test",
            "length_m": 1200.0, "composite_score": 0.10,
            "coordinates": [[0, 0], [0, 0.005]],
        }
        segmento_corta = {
            "source_node": 1, "target_node": 4, "name": "Calle Test Corta",
            "length_m": 1000.0, "composite_score": 0.90,
            "coordinates": [[0, 0], [0, 0.005]],
        }
        return {
            "ruta_segura": {
                "nodos": [1, 2, 3, 4], "segmentos": [segmento_segura],
                "longitud_total_m": 1200.0, "security_score": 90, "categoria": "Segura",
            },
            "ruta_corta": {
                "nodos": [1, 4], "segmentos": [segmento_corta],
                "longitud_total_m": 1000.0, "security_score": 10, "categoria": "Riesgosa",
            },
        }


def make_failing_service(excepcion):
    """Crea una version falsa del RoutingService que siempre lanza la excepcion dada."""
    class FakeRoutingServiceFail:
        def __init__(self, db=None, graph_dao=None):
            pass

        def calcular_rutas(self, **kwargs):
            raise excepcion
    return FakeRoutingServiceFail


@pytest.fixture
def client():
    return TestClient(app)


# Coordenadas de prueba: ~1.5km de distancia, dentro de los limites validos
ORIGEN = {"lat": -12.046, "lon": -77.043}
DESTINO = {"lat": -12.056, "lon": -77.033}


def test_origen_igual_a_destino_retorna_400(client):
    body = {"origin": ORIGEN, "destination": {"lat": ORIGEN["lat"] + 0.0001, "lon": ORIGEN["lon"]}}
    resp = client.post("/api/v1/route", json=body)
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "INVALID_COORDINATES"


def test_distancia_excede_maximo_retorna_400(client):
    body = {"origin": {"lat": -12.0, "lon": -77.0}, "destination": {"lat": -12.3, "lon": -77.0}}
    resp = client.post("/api/v1/route", json=body)
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "INVALID_COORDINATES"


def test_payload_invalido_retorna_422(client):
    body = {"origin": ORIGEN}  # falta "destination"
    resp = client.post("/api/v1/route", json=body)
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


def test_ruta_valida_retorna_200_con_estructura_esperada(client, monkeypatch):
    monkeypatch.setattr(route_endpoint, "RoutingService", FakeRoutingServiceOK)

    body = {"origin": ORIGEN, "destination": DESTINO}
    resp = client.post("/api/v1/route", json=body)

    assert resp.status_code == 200
    data = resp.json()
    assert data["safe_route"]["summary"]["security_score"] == 90
    assert data["safe_route"]["summary"]["category"] == "Segura"
    assert data["shortest_route"]["summary"]["security_score"] == 10
    assert data["comparison"] is not None
    assert len(data["safe_route"]["geojson"]["features"]) == 1


def test_include_shortest_false_omite_ruta_corta_y_comparacion(client, monkeypatch):
    monkeypatch.setattr(route_endpoint, "RoutingService", FakeRoutingServiceOK)

    body = {"origin": ORIGEN, "destination": DESTINO, "include_shortest": False}
    resp = client.post("/api/v1/route", json=body)

    assert resp.status_code == 200
    data = resp.json()
    assert data["shortest_route"] is None
    assert data["comparison"] is None


def test_no_existe_ruta_retorna_404(client, monkeypatch):
    fake = make_failing_service(ValueError("No existe ruta entre los puntos seleccionados"))
    monkeypatch.setattr(route_endpoint, "RoutingService", fake)

    resp = client.post("/api/v1/route", json={"origin": ORIGEN, "destination": DESTINO})
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "NO_ROUTE_FOUND"


def test_grafo_vacio_retorna_503(client, monkeypatch):
    fake = make_failing_service(ValueError("El grafo está vacío. Ejecuta primero ingest_street_graph.py"))
    monkeypatch.setattr(route_endpoint, "RoutingService", fake)

    resp = client.post("/api/v1/route", json={"origin": ORIGEN, "destination": DESTINO})
    assert resp.status_code == 503
    assert resp.json()["error"]["code"] == "SERVICE_UNAVAILABLE"


def test_error_inesperado_retorna_500(client, monkeypatch):
    fake = make_failing_service(RuntimeError("boom"))
    monkeypatch.setattr(route_endpoint, "RoutingService", fake)

    resp = client.post("/api/v1/route", json={"origin": ORIGEN, "destination": DESTINO})
    assert resp.status_code == 500
    assert resp.json()["error"]["code"] == "INTERNAL_ERROR"
