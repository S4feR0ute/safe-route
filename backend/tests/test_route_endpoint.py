import pytest
from fastapi.testclient import TestClient

from api_app import app
from app.db.session import get_db
from app.core.service_container import ServiceContainer, get_service_container
from app.core.exceptions import EmptyGraphError, NoRouteError
import app.api.route_endpoint as route_endpoint


def fake_get_db():
    yield None


app.dependency_overrides[get_db] = fake_get_db


def make_fake_container(resultado=None, excepcion=None):
    """Crea un ServiceContainer falso que devuelve resultado o lanza excepcion."""
    class FakeRoutingService:
        def calcular_rutas(self, **kwargs):
            if excepcion:
                raise excepcion
            return resultado

    class FakeContainer:
        def get_routing_service(self):
            return FakeRoutingService()

    return FakeContainer()


RESULTADO_OK = {
    "ruta_segura": {
        "nodos": [1, 2, 3, 4],
        "segmentos": [{
            "source_node": 1, "target_node": 2, "name": "Calle Test",
            "length_m": 1200.0, "composite_score": 0.10,
            "coordinates": [[0, 0], [0, 0.005]],
        }],
        "longitud_total_m": 1200.0,
        "security_score": 90,
        "categoria": "Segura",
    },
    "ruta_corta": {
        "nodos": [1, 4],
        "segmentos": [{
            "source_node": 1, "target_node": 4, "name": "Calle Corta",
            "length_m": 1000.0, "composite_score": 0.90,
            "coordinates": [[0, 0], [0, 0.005]],
        }],
        "longitud_total_m": 1000.0,
        "security_score": 10,
        "categoria": "Riesgosa",
    },
}


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


def test_ruta_valida_retorna_200_con_estructura_esperada(client):
    app.dependency_overrides[get_service_container] = lambda: make_fake_container(resultado=RESULTADO_OK)

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


def test_include_shortest_false_omite_ruta_corta_y_comparacion(client):
    app.dependency_overrides[get_service_container] = lambda: make_fake_container(resultado=RESULTADO_OK)

    body = {"origin": ORIGEN, "destination": DESTINO, "include_shortest": False}
    resp = client.post("/api/v1/route", json=body)

    app.dependency_overrides.pop(get_service_container, None)

    assert resp.status_code == 200
    data = resp.json()
    assert data["shortest_route"] is None
    assert data["comparison"] is None


def test_no_existe_ruta_retorna_404(client):
    app.dependency_overrides[get_service_container] = lambda: make_fake_container(excepcion=NoRouteError("sin ruta"))

    resp = client.post("/api/v1/route", json={"origin": ORIGEN, "destination": DESTINO})

    app.dependency_overrides.pop(get_service_container, None)

    assert resp.status_code == 404


def test_grafo_vacio_retorna_503(client):
    app.dependency_overrides[get_service_container] = lambda: make_fake_container(excepcion=EmptyGraphError("grafo vacio"))

    resp = client.post("/api/v1/route", json={"origin": ORIGEN, "destination": DESTINO})

    app.dependency_overrides.pop(get_service_container, None)

    assert resp.status_code == 503


def test_error_inesperado_retorna_500(client):
    app.dependency_overrides[get_service_container] = lambda: make_fake_container(excepcion=RuntimeError("boom"))

    resp = client.post("/api/v1/route", json={"origin": ORIGEN, "destination": DESTINO})

    app.dependency_overrides.pop(get_service_container, None)

    assert resp.status_code == 500
