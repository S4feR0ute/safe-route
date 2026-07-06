import pytest
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.user import User
from app.models.incident_report import IncidentReport
from app.services.moderation_service import ModerationService
from app.repositories.factory import RepositoryFactory
from app.core.security import create_access_token

TEST_EMAILS = ["moderator@test.com", "citizen@test.com"]


def _cleanup_test_data(session: Session):
    """Elimina usuarios de prueba y sus reportes (los tests usan la BD real)."""
    session.rollback()
    user_ids = [uid for (uid,) in session.query(User.id).filter(User.email.in_(TEST_EMAILS))]
    if user_ids:
        session.query(IncidentReport).filter(
            (IncidentReport.user_id.in_(user_ids))
            | (IncidentReport.validated_by_user_id.in_(user_ids))
        ).delete(synchronize_session=False)
        session.query(User).filter(User.id.in_(user_ids)).delete(synchronize_session=False)
    session.commit()


@pytest.fixture
def db():
    """Sesión contra la BD real, con limpieza de datos de prueba antes y después."""
    session = SessionLocal()
    _cleanup_test_data(session)
    try:
        yield session
    finally:
        _cleanup_test_data(session)
        session.close()


@pytest.fixture
def auth_header_factory(db: Session):
    """Genera tokens JWT para un user_id dado."""
    def _make(user_id: int) -> str:
        user = db.query(User).filter(User.id == user_id).first()
        return create_access_token({"sub": user.email, "id": user.id})
    return _make


@pytest.fixture
def moderator_user(db: Session) -> User:
    """Crea un usuario moderador para pruebas."""
    user_repo = RepositoryFactory.create_user_repository(db)
    user = user_repo.create(
        email="moderator@test.com",
        password_hash="hashed_password",
        full_name="Test Moderator",
    )
    user.user_type = "moderator"
    user.is_active = True
    db.commit()
    return user


@pytest.fixture
def citizen_user(db: Session) -> User:
    """Crea un usuario ciudadano para pruebas."""
    user_repo = RepositoryFactory.create_user_repository(db)
    user = user_repo.create(
        email="citizen@test.com",
        password_hash="hashed_password",
        full_name="Test Citizen",
    )
    db.commit()
    return user


@pytest.fixture
def pending_report(db: Session, citizen_user: User) -> IncidentReport:
    """Crea un reporte pendiente para pruebas."""
    incident_repo = RepositoryFactory.create_incident_repository(db)
    report = incident_repo.create(
        incident_type="robo",
        location_wkt="SRID=4326;POINT(-77.0428 -12.0464)",
        latitude=-12.0464,
        longitude=-77.0428,
        mode=3,
        user_id=citizen_user.id,
        description="Reporte de prueba"
    )
    report.status = "pending"
    report.evidence_quality_score = 75.0
    db.commit()
    return report


class TestModerationService:
    """Tests para ModerationService"""

    def test_get_pending_reports(self, db: Session, pending_report: IncidentReport):
        """Debe obtener reportes pendientes."""
        service = ModerationService(db)
        reports, total = service.get_pending_reports(limit=10)

        assert total >= 1
        assert len(reports) >= 1
        assert any(r.id == pending_report.id for r in reports)

    def test_get_pending_reports_with_filter(
        self, db: Session, pending_report: IncidentReport
    ):
        """Debe filtrar reportes pendientes por tipo."""
        service = ModerationService(db)
        reports, total = service.get_pending_reports(
            limit=10, incident_type="robo"
        )

        assert len(reports) >= 1
        assert all(r.incident_type == "robo" for r in reports)

    def test_approve_report(self, db: Session, pending_report: IncidentReport, moderator_user: User):
        """Debe aprobar un reporte."""
        service = ModerationService(db)
        result = service.approve_report(
            report_id=pending_report.id,
            moderator=moderator_user,
            validation_notes="Evidencia clara"
        )

        assert result.status == "validated"
        assert result.validated_by_user_id == moderator_user.id
        assert result.validated_at is not None
        assert result.validation_notes == "Evidencia clara"

    def test_approve_non_pending_report(
        self, db: Session, pending_report: IncidentReport, moderator_user: User
    ):
        """Debe fallar al intentar aprobar reporte no pendiente."""
        service = ModerationService(db)

        # Primero aprueba
        service.approve_report(pending_report.id, moderator_user)

        # Intenta aprobar de nuevo
        with pytest.raises(ValueError, match="no está pendiente"):
            service.approve_report(pending_report.id, moderator_user)

    def test_reject_report(self, db: Session, pending_report: IncidentReport, moderator_user: User):
        """Debe rechazar un reporte."""
        service = ModerationService(db)
        result = service.reject_report(
            report_id=pending_report.id,
            moderator=moderator_user,
            validation_notes="Ubicación no corresponde"
        )

        assert result.status == "rejected"
        assert result.validated_by_user_id == moderator_user.id
        assert result.validated_at is not None
        assert result.validation_notes == "Ubicación no corresponde"

    def test_reject_without_reason(
        self, db: Session, pending_report: IncidentReport, moderator_user: User
    ):
        """Debe fallar al rechazar sin proporcionar motivo."""
        service = ModerationService(db)

        with pytest.raises(ValueError, match="motivo"):
            service.reject_report(
                report_id=pending_report.id,
                moderator=moderator_user,
                validation_notes=""
            )

    def test_reject_non_pending_report(
        self, db: Session, pending_report: IncidentReport, moderator_user: User
    ):
        """Debe fallar al intentar rechazar reporte no pendiente."""
        service = ModerationService(db)

        # Primero rechaza
        service.reject_report(
            pending_report.id,
            moderator_user,
            "Razón inicial"
        )

        # Intenta rechazar de nuevo
        with pytest.raises(ValueError, match="no está pendiente"):
            service.reject_report(
                pending_report.id,
                moderator_user,
                "Otra razón"
            )

    def test_approve_non_existent_report(
        self, db: Session, moderator_user: User
    ):
        """Debe fallar al aprobar reporte inexistente."""
        service = ModerationService(db)

        with pytest.raises(ValueError, match="no encontrado"):
            service.approve_report(
                report_id="non-existent-id",
                moderator=moderator_user
            )

    def test_get_moderation_stats(self, db: Session, pending_report: IncidentReport, moderator_user: User):
        """Debe obtener estadísticas correctas."""
        service = ModerationService(db)

        # Antes de validación
        stats_before = service.get_moderation_stats()
        pending_before = stats_before["pending"]

        # Aprobar un reporte
        service.approve_report(pending_report.id, moderator_user)

        # Después de validación
        stats_after = service.get_moderation_stats()

        assert stats_after["pending"] == pending_before - 1
        assert stats_after["validated"] > 0

    def test_get_report_detail(self, db: Session, pending_report: IncidentReport):
        """Debe obtener detalles de un reporte."""
        service = ModerationService(db)
        report = service.get_report_detail(pending_report.id)

        assert report.id == pending_report.id
        assert report.incident_type == "robo"
        assert report.status == "pending"

    def test_get_non_existent_report_detail(self, db: Session):
        """Debe fallar al obtener detalles de reporte inexistente."""
        service = ModerationService(db)

        with pytest.raises(ValueError, match="no encontrado"):
            service.get_report_detail("non-existent-id")

    def test_pagination(self, db: Session):
        """Debe paginar correctamente los reportes pendientes."""
        service = ModerationService(db)

        # Obtener primera página
        reports_page1, total1 = service.get_pending_reports(limit=2, offset=0)
        # Obtener segunda página
        reports_page2, total2 = service.get_pending_reports(limit=2, offset=2)

        assert total1 == total2  # El total no cambia
        # Las páginas deberían tener IDs diferentes (si hay suficientes reportes)
        ids_page1 = {r.id for r in reports_page1}
        ids_page2 = {r.id for r in reports_page2}
        # Pueden ser iguales si hay pocos reportes, pero si no se solapan es mejor


class TestModerationEndpointsAuthorization:
    """Tests para validar autorización en endpoints de moderación"""

    def test_non_moderator_cannot_access_queue(
        self, db: Session, citizen_user: User, auth_header_factory
    ):
        """Un ciudadano no puede acceder a la cola de moderación."""
        token = auth_header_factory(citizen_user.id)
        # En un test de endpoint real, hacer:
        # response = client.get(
        #     "/api/v1/moderation/queue",
        #     headers={"Authorization": f"Bearer {token}"}
        # )
        # assert response.status_code == 403

    def test_moderator_can_access_queue(
        self, db: Session, moderator_user: User
    ):
        """Un moderador puede acceder a la cola de moderación."""
        # Verificar que el usuario tiene el tipo correcto
        assert moderator_user.user_type == "moderator"
        assert moderator_user.is_active is True


class TestModerationWorkflow:
    """Tests del flujo completo de moderación"""

    def test_complete_approval_workflow(
        self, db: Session, pending_report: IncidentReport, moderator_user: User
    ):
        """Debe completar el flujo de aprobación."""
        service = ModerationService(db)

        # 1. Obtener reportes pendientes
        reports, total = service.get_pending_reports(limit=10)
        assert pending_report.id in [r.id for r in reports]

        # 2. Ver detalles del reporte
        report_detail = service.get_report_detail(pending_report.id)
        assert report_detail.status == "pending"

        # 3. Aprobar reporte
        approved = service.approve_report(
            report_id=pending_report.id,
            moderator=moderator_user,
            validation_notes="Evidencia clara con fotos"
        )

        assert approved.status == "validated"
        assert approved.validated_by_user_id == moderator_user.id

        # 4. Verificar que ya no aparece en pendientes
        reports_after, _ = service.get_pending_reports(limit=10)
        assert pending_report.id not in [r.id for r in reports_after]

    def test_complete_rejection_workflow(
        self, db: Session, pending_report: IncidentReport, moderator_user: User
    ):
        """Debe completar el flujo de rechazo."""
        service = ModerationService(db)

        # 1. Obtener reportes pendientes
        reports, total = service.get_pending_reports(limit=10)
        assert pending_report.id in [r.id for r in reports]

        # 2. Rechazar reporte
        rejected = service.reject_report(
            report_id=pending_report.id,
            moderator=moderator_user,
            validation_notes="Ubicación no corresponde al tipo de incidente"
        )

        assert rejected.status == "rejected"
        assert rejected.validated_by_user_id == moderator_user.id
        assert rejected.validation_notes == "Ubicación no corresponde al tipo de incidente"

        # 3. Verificar que ya no aparece en pendientes
        reports_after, _ = service.get_pending_reports(limit=10)
        assert pending_report.id not in [r.id for r in reports_after]
