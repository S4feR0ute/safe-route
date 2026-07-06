import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from datetime import datetime

from api_app import app
from app.db.session import get_db
from app.core.service_container import ServiceContainer, get_service_container
from app.core.auth_helper import get_current_user_optional, get_moderator
from app.core.exceptions import ReportNotFoundError, InvalidReportStateError


def fake_get_db():
    yield None


app.dependency_overrides[get_db] = fake_get_db


def make_fake_report(mode: int, user_id=None, status="pending"):
    report = MagicMock()
    report.id = "test-report-uuid-001"
    report.incident_type = "robo"
    report.latitude = -12.046
    report.longitude = -77.043
    report.description = "Descripcion de prueba"
    report.occurred_at = None
    report.status = status
    report.mode = mode
    report.user_id = user_id
    report.created_at = datetime(2026, 7, 6, 10, 0, 0)
    report.updated_at = datetime(2026, 7, 6, 10, 0, 0)
    report.validated_at = None
    report.validated_by_user_id = None
    return report


def make_fake_user(user_id=1, user_type="citizen"):
    user = MagicMock()
    user.id = user_id
    user.user_type = user_type
    user.is_active = True
    return user


def make_fake_container_report(report=None, excepcion=None):
    class FakeReportService:
        async def create_report(self, **kwargs):
            if excepcion:
                raise excepcion
            return report

    class FakeContainer:
        def get_report_service(self):
            return FakeReportService()
        def get_moderation_service(self):
            return MagicMock()

    return FakeContainer()


def make_fake_container_moderation(report=None, excepcion=None):
    class FakeModerationService:
        def approve_report(self, **kwargs):
            if excepcion:
                raise excepcion
            return report
        def reject_report(self, **kwargs):
            if excepcion:
                raise excepcion
            return report

    class FakeContainer:
        def get_report_service(self):
            return MagicMock()
        def get_moderation_service(self):
            return FakeModerationService()

    return FakeContainer()


@pytest.fixture
def client():
    return TestClient(app)


# --- MODO 3: CREACION CON ARCHIVO ---

def test_modo3_reporte_con_archivo_valido_retorna_201(client):
    """Modo 3: usuario autenticado con archivo valido crea reporte con mode=3."""
    user = make_fake_user(user_id=42)
    reporte = make_fake_report(mode=3, user_id=42)

    app.dependency_overrides[get_service_container] = lambda: make_fake_container_report(report=reporte)
    app.dependency_overrides[get_current_user_optional] = lambda: user

    resp = client.post("/api/v1/reports",
        data={
            "incident_type": "robo",
            "latitude": -12.046,
            "longitude": -77.043,
        },
        files={"file": ("evidencia.jpg", b"fake image content", "image/jpeg")}
    )

    app.dependency_overrides.pop(get_service_container, None)
    app.dependency_overrides.pop(get_current_user_optional, None)

    assert resp.status_code == 201
    assert resp.json()["mode"] == 3


def test_modo3_anonimo_con_archivo_retorna_400(client):
    """Modo 3: usuario anonimo no puede adjuntar archivos."""
    app.dependency_overrides[get_service_container] = lambda: make_fake_container_report(
        excepcion=ValueError("Adjuntar archivos requiere una cuenta (modo 3).")
    )
    app.dependency_overrides[get_current_user_optional] = lambda: None

    resp = client.post("/api/v1/reports",
        data={
            "incident_type": "robo",
            "latitude": -12.046,
            "longitude": -77.043,
        },
        files={"file": ("evidencia.jpg", b"fake image content", "image/jpeg")}
    )

    app.dependency_overrides.pop(get_service_container, None)
    app.dependency_overrides.pop(get_current_user_optional, None)

    assert resp.status_code == 400


def test_modo3_archivo_tipo_no_permitido_retorna_400(client):
    """Modo 3: archivo de tipo no permitido (ej. .exe) debe rechazarse."""
    user = make_fake_user(user_id=42)
    app.dependency_overrides[get_service_container] = lambda: make_fake_container_report(
        excepcion=ValueError("Tipo de archivo no permitido")
    )
    app.dependency_overrides[get_current_user_optional] = lambda: user

    resp = client.post("/api/v1/reports",
        data={
            "incident_type": "robo",
            "latitude": -12.046,
            "longitude": -77.043,
        },
        files={"file": ("virus.exe", b"fake exe content", "application/octet-stream")}
    )

    app.dependency_overrides.pop(get_service_container, None)
    app.dependency_overrides.pop(get_current_user_optional, None)

    assert resp.status_code == 400


def test_modo3_archivo_demasiado_grande_retorna_400(client):
    """Modo 3: archivo que excede el limite de 10MB debe rechazarse."""
    user = make_fake_user(user_id=42)
    app.dependency_overrides[get_service_container] = lambda: make_fake_container_report(
        excepcion=ValueError("El archivo excede el tamaño máximo permitido")
    )
    app.dependency_overrides[get_current_user_optional] = lambda: user

    resp = client.post("/api/v1/reports",
        data={
            "incident_type": "robo",
            "latitude": -12.046,
            "longitude": -77.043,
        },
        files={"file": ("grande.pdf", b"x" * 100, "application/pdf")}
    )

    app.dependency_overrides.pop(get_service_container, None)
    app.dependency_overrides.pop(get_current_user_optional, None)

    assert resp.status_code == 400


# --- MODERACION ---

def test_moderador_aprueba_reporte_retorna_200(client):
    """Moderador puede aprobar un reporte pendiente."""
    moderador = make_fake_user(user_id=99, user_type="moderator")
    reporte_aprobado = make_fake_report(mode=2, user_id=42, status="validated")

    app.dependency_overrides[get_service_container] = lambda: make_fake_container_moderation(report=reporte_aprobado)
    app.dependency_overrides[get_moderator] = lambda: moderador

    resp = client.patch("/api/v1/moderation/test-report-uuid-001/approve",
        json={"status": "validated", "reason": "Reporte verificado correctamente"}
    )

    app.dependency_overrides.pop(get_service_container, None)
    app.dependency_overrides.pop(get_moderator, None)

    assert resp.status_code == 200
    assert resp.json()["status"] == "validated"


def test_moderador_rechaza_reporte_retorna_200(client):
    """Moderador puede rechazar un reporte pendiente."""
    moderador = make_fake_user(user_id=99, user_type="moderator")
    reporte_rechazado = make_fake_report(mode=2, user_id=42, status="rejected")

    app.dependency_overrides[get_service_container] = lambda: make_fake_container_moderation(report=reporte_rechazado)
    app.dependency_overrides[get_moderator] = lambda: moderador

    resp = client.patch("/api/v1/moderation/test-report-uuid-001/reject",
        json={"status": "rejected", "reason": "Informacion insuficiente"}
    )

    app.dependency_overrides.pop(get_service_container, None)
    app.dependency_overrides.pop(get_moderator, None)

    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"


def test_moderacion_reporte_no_encontrado_retorna_404(client):
    """Intentar moderar un reporte inexistente retorna 404."""
    moderador = make_fake_user(user_id=99, user_type="moderator")

    app.dependency_overrides[get_service_container] = lambda: make_fake_container_moderation(
        excepcion=ReportNotFoundError("Reporte no encontrado")
    )
    app.dependency_overrides[get_moderator] = lambda: moderador

    resp = client.patch("/api/v1/moderation/uuid-inexistente/approve",
        json={"status": "validated"}
    )

    app.dependency_overrides.pop(get_service_container, None)
    app.dependency_overrides.pop(get_moderator, None)

    assert resp.status_code == 404


def test_usuario_normal_no_puede_moderar_retorna_403(client):
    """Usuario sin rol de moderador recibe 403 al intentar moderar."""
    app.dependency_overrides[get_moderator] = lambda: (_ for _ in ()).throw(
        __import__('fastapi').HTTPException(status_code=403, detail="Acceso restringido")
    )

    resp = client.patch("/api/v1/moderation/test-report-uuid-001/approve",
        json={"status": "validated"}
    )

    app.dependency_overrides.pop(get_moderator, None)

    assert resp.status_code == 403
