import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime

from api_app import app
from app.db.session import get_db
from app.core.service_container import ServiceContainer, get_service_container
from app.core.auth_helper import get_current_user_optional


def fake_get_db():
    yield None


app.dependency_overrides[get_db] = fake_get_db


def make_fake_report(mode: int, user_id=None, incident_type="robo",
                     lat=-12.046, lon=-77.043, occurred_at=None):
    """Crea un objeto reporte falso con los campos que devuelve ReportResponse."""
    report = MagicMock()
    report.id = "test-report-uuid-001"
    report.incident_type = incident_type
    report.latitude = lat
    report.longitude = lon
    report.description = "Descripcion de prueba"
    report.occurred_at = occurred_at
    report.status = "pending"
    report.mode = mode
    report.user_id = user_id
    report.created_at = datetime(2026, 7, 6, 10, 0, 0)
    report.updated_at = datetime(2026, 7, 6, 10, 0, 0)
    report.validated_at = None
    report.validated_by_user_id = None
    return report


def make_fake_user(user_id=1, user_type="citizen"):
    """Crea un usuario falso para simular autenticacion."""
    user = MagicMock()
    user.id = user_id
    user.user_type = user_type
    user.is_active = True
    return user


def make_fake_container(report=None, excepcion=None):
    """Crea un ServiceContainer falso que controla el ReportService."""
    class FakeReportService:
        async def create_report(self, **kwargs):
            if excepcion:
                raise excepcion
            return report

    class FakeContainer:
        def get_report_service(self):
            return FakeReportService()

    return FakeContainer()


@pytest.fixture
def client():
    return TestClient(app)


# --- MODO 1: USUARIO ANONIMO ---

def test_modo1_reporte_anonimo_valido_retorna_201(client):
    """Modo 1: usuario anonimo puede crear reporte con campos minimos."""
    reporte = make_fake_report(mode=1, user_id=None)
    app.dependency_overrides[get_service_container] = lambda: make_fake_container(report=reporte)
    app.dependency_overrides[get_current_user_optional] = lambda: None

    resp = client.post("/api/v1/reports", data={
        "incident_type": "robo",
        "latitude": -12.046,
        "longitude": -77.043,
    })

    app.dependency_overrides.pop(get_service_container, None)
    app.dependency_overrides.pop(get_current_user_optional, None)

    assert resp.status_code == 201
    data = resp.json()
    assert data["mode"] == 1
    assert data["user_id"] is None
    assert data["status"] == "pending"


def test_modo1_tipo_incidente_invalido_retorna_400(client):
    """Modo 1: tipo de incidente no reconocido debe rechazarse."""
    app.dependency_overrides[get_service_container] = lambda: make_fake_container(
        excepcion=ValueError("Tipo de incidente inválido")
    )
    app.dependency_overrides[get_current_user_optional] = lambda: None

    resp = client.post("/api/v1/reports", data={
        "incident_type": "tipo_inexistente",
        "latitude": -12.046,
        "longitude": -77.043,
    })

    app.dependency_overrides.pop(get_service_container, None)
    app.dependency_overrides.pop(get_current_user_optional, None)

    assert resp.status_code == 400


def test_modo1_anonimo_con_fecha_retorna_400(client):
    """Modo 1: usuario anonimo no puede indicar fecha del incidente."""
    app.dependency_overrides[get_service_container] = lambda: make_fake_container(
        excepcion=ValueError("Indicar la fecha del incidente requiere una cuenta (modo 2).")
    )
    app.dependency_overrides[get_current_user_optional] = lambda: None

    resp = client.post("/api/v1/reports", data={
        "incident_type": "robo",
        "latitude": -12.046,
        "longitude": -77.043,
        "incident_date": "2026-07-01T10:00:00",
    })

    app.dependency_overrides.pop(get_service_container, None)
    app.dependency_overrides.pop(get_current_user_optional, None)

    assert resp.status_code == 400


def test_modo1_fecha_invalida_retorna_400(client):
    """Modo 1: fecha con formato incorrecto debe rechazarse antes de llegar al servicio."""
    app.dependency_overrides[get_current_user_optional] = lambda: None

    resp = client.post("/api/v1/reports", data={
        "incident_type": "robo",
        "latitude": -12.046,
        "longitude": -77.043,
        "incident_date": "no-es-una-fecha",
    })

    app.dependency_overrides.pop(get_current_user_optional, None)

    assert resp.status_code == 400


# --- MODO 2: USUARIO AUTENTICADO ---

def test_modo2_reporte_autenticado_valido_retorna_201(client):
    """Modo 2: usuario autenticado puede crear reporte con modo=2."""
    user = make_fake_user(user_id=42)
    reporte = make_fake_report(mode=2, user_id=42)

    app.dependency_overrides[get_service_container] = lambda: make_fake_container(report=reporte)
    app.dependency_overrides[get_current_user_optional] = lambda: user

    resp = client.post("/api/v1/reports", data={
        "incident_type": "asalto",
        "latitude": -12.056,
        "longitude": -77.033,
        "description": "Asalto en la esquina",
    })

    app.dependency_overrides.pop(get_service_container, None)
    app.dependency_overrides.pop(get_current_user_optional, None)

    assert resp.status_code == 201
    data = resp.json()
    assert data["mode"] == 2
    assert data["user_id"] == 42
    assert data["status"] == "pending"


def test_modo2_reporte_con_fecha_valida_retorna_201(client):
    """Modo 2: usuario autenticado puede indicar la fecha del incidente."""
    user = make_fake_user(user_id=42)
    reporte = make_fake_report(
        mode=2, user_id=42,
        occurred_at=datetime(2026, 7, 1, 21, 30, 0)
    )

    app.dependency_overrides[get_service_container] = lambda: make_fake_container(report=reporte)
    app.dependency_overrides[get_current_user_optional] = lambda: user

    resp = client.post("/api/v1/reports", data={
        "incident_type": "violencia",
        "latitude": -12.056,
        "longitude": -77.033,
        "incident_date": "2026-07-01T21:30:00",
    })

    app.dependency_overrides.pop(get_service_container, None)
    app.dependency_overrides.pop(get_current_user_optional, None)

    assert resp.status_code == 201
    data = resp.json()
    assert data["mode"] == 2
    assert data["occurred_at"] is not None


def test_modo2_fecha_en_el_futuro_retorna_400(client):
    """Modo 2: fecha del incidente en el futuro debe rechazarse."""
    user = make_fake_user(user_id=42)

    app.dependency_overrides[get_service_container] = lambda: make_fake_container(
        excepcion=ValueError("La fecha del incidente no puede estar en el futuro")
    )
    app.dependency_overrides[get_current_user_optional] = lambda: user

    resp = client.post("/api/v1/reports", data={
        "incident_type": "robo",
        "latitude": -12.056,
        "longitude": -77.033,
        "incident_date": "2099-01-01T00:00:00",
    })

    app.dependency_overrides.pop(get_service_container, None)
    app.dependency_overrides.pop(get_current_user_optional, None)

    assert resp.status_code == 400


def test_modo2_tipo_incidente_invalido_retorna_400(client):
    """Modo 2: tipo de incidente invalido tambien se rechaza con token."""
    user = make_fake_user(user_id=42)

    app.dependency_overrides[get_service_container] = lambda: make_fake_container(
        excepcion=ValueError("Tipo de incidente inválido")
    )
    app.dependency_overrides[get_current_user_optional] = lambda: user

    resp = client.post("/api/v1/reports", data={
        "incident_type": "tipo_invalido",
        "latitude": -12.056,
        "longitude": -77.033,
    })

    app.dependency_overrides.pop(get_service_container, None)
    app.dependency_overrides.pop(get_current_user_optional, None)

    assert resp.status_code == 400


def test_error_interno_retorna_500(client):
    """Cualquier error inesperado del servicio debe retornar 500."""
    app.dependency_overrides[get_service_container] = lambda: make_fake_container(
        excepcion=RuntimeError("error inesperado")
    )
    app.dependency_overrides[get_current_user_optional] = lambda: None

    resp = client.post("/api/v1/reports", data={
        "incident_type": "robo",
        "latitude": -12.046,
        "longitude": -77.043,
    })

    app.dependency_overrides.pop(get_service_container, None)
    app.dependency_overrides.pop(get_current_user_optional, None)

    assert resp.status_code == 500
