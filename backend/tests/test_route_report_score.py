import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session as SQLASession
from datetime import datetime

from app.db.session import engine
from app.models.street_network import StreetSegment, StreetNode
from app.models.risk_score import RiskScore
from app.models.incident_report import IncidentReport
from app.models.user import User  # necesario para que SQLAlchemy registre la relacion IncidentReport->User
from app.models.report_document import ReportDocument  # necesario para que SQLAlchemy registre la relacion IncidentReport->ReportDocument
from app.services.score_calculator_service import ScoreCalculatorService


@pytest.fixture
def db(monkeypatch):
    """
    Sesion de BD con commit desactivado y rollback al final.
    Los datos reales de produccion quedan intactos siempre.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = SQLASession(bind=connection)
    monkeypatch.setattr(session, "commit", session.flush)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(autouse=True)
def datos_sinteticos(db):
    """
    Inserta una calle de prueba en coordenadas (0, 0) con distrito
    de alta criminalidad. Sin reportes al inicio.
    """
    cleanup_sql = """
    DELETE FROM risk_scores WHERE segment_id IN (8000001);
    DELETE FROM street_segments WHERE id IN (8000001);
    DELETE FROM street_nodes WHERE node_id IN (8000001, 8000002);
    DELETE FROM district_crime_stats WHERE district_ubigeo = '888801';
    DELETE FROM incident_reports WHERE id = 'test-report-saf80-001';
    """
    setup_sql = """
    INSERT INTO district_crime_stats
        (district_ubigeo, district_name, total_incidents_count, violent_incidents_count, weighted_crime_rate)
    VALUES ('888801', 'Distrito SAF80', 10, 8, 0.70);

    INSERT INTO street_nodes (node_id, geometry, lat, lon) VALUES
    (8000001, ST_SetSRID(ST_MakePoint(0, 0), 4326), 0, 0),
    (8000002, ST_SetSRID(ST_MakePoint(0, 0.001), 4326), 0.001, 0);

    INSERT INTO street_segments
        (id, osm_way_id, geometry, name, length_m, highway_type, oneway,
         source_node_id, target_node_id, district_ubigeo)
    VALUES (8000001, 8000001,
        ST_SetSRID(ST_MakeLine(ST_MakePoint(0,0), ST_MakePoint(0,0.001)), 4326),
        'Calle SAF80', 111.0, 'residential', false, 8000001, 8000002, '888801');
    """
    db.execute(text(cleanup_sql))
    db.execute(text(setup_sql))
    db.flush()
    yield
    db.execute(text(cleanup_sql))


def obtener_score(db, segment_id):
    sql = text("""
        SELECT district_score, context_score, report_score, composite_score
        FROM risk_scores WHERE segment_id = :sid
    """)
    row = db.execute(sql, {"sid": segment_id}).fetchone()
    assert row is not None, f"No se encontro score para segmento {segment_id}"
    return row


def insertar_reporte_validado(db, lat=0.0, lon=0.0, incident_type="robo",
                               severity="high"):
    """Inserta un reporte validado en las coordenadas dadas."""
    sql = text("""
        INSERT INTO incident_reports
            (id, incident_type, location, latitude, longitude,
             status, mode, severity_level, created_at, updated_at)
        VALUES (
            'test-report-saf80-001', :tipo,
            ST_SetSRID(ST_MakePoint(:lon, :lat), 4326),
            :lat, :lon, 'validated', 1, :sev,
            NOW(), NOW()
        )
    """)
    db.execute(sql, {"tipo": incident_type, "lat": lat, "lon": lon, "sev": severity})
    db.flush()


def test_sin_reportes_report_score_es_cero(db):
    """Sin reportes validados cercanos, el report_score debe ser 0."""
    service = ScoreCalculatorService(db=db)
    service.calculate_all_scores()

    _, _, report_score, _ = obtener_score(db, 8000001)
    assert report_score == 0.0


def test_con_reporte_validado_report_score_mayor_que_cero(db):
    """Con un reporte validado cercano, el report_score debe ser mayor que 0."""
    insertar_reporte_validado(db, lat=0.0, lon=0.0, incident_type="robo", severity="high")

    service = ScoreCalculatorService(db=db)
    service.calculate_all_scores()

    _, _, report_score, _ = obtener_score(db, 8000001)
    assert report_score > 0.0, f"Se esperaba report_score > 0, pero fue {report_score}"


def test_reporte_validado_cambia_composite_score(db):
    """El composite_score con reporte debe diferir del composite sin reporte."""
    service = ScoreCalculatorService(db=db)
    service.calculate_all_scores()
    _, _, _, composite_sin = obtener_score(db, 8000001)

    insertar_reporte_validado(db, lat=0.0, lon=0.0, incident_type="robo", severity="high")
    service.calculate_all_scores()
    _, _, _, composite_con = obtener_score(db, 8000001)

    assert composite_sin != composite_con, (
        f"Se esperaba que el composite cambiara. "
        f"Sin reporte: {composite_sin}, con reporte: {composite_con}"
    )


def test_reporte_pending_no_afecta_score(db):
    """Un reporte en estado 'pending' (no validado) NO debe afectar el score."""
    sql = text("""
        INSERT INTO incident_reports
            (id, incident_type, location, latitude, longitude,
             status, mode, severity_level, created_at, updated_at)
        VALUES (
            'test-report-saf80-001', 'robo',
            ST_SetSRID(ST_MakePoint(0, 0), 4326),
            0, 0, 'pending', 1, 'high', NOW(), NOW()
        )
    """)
    db.execute(sql)
    db.flush()

    service = ScoreCalculatorService(db=db)
    service.calculate_all_scores()

    _, _, report_score, _ = obtener_score(db, 8000001)
    assert report_score == 0.0, (
        f"Un reporte 'pending' no deberia afectar el score. "
        f"report_score fue {report_score}"
    )


def test_reporte_fuera_del_radio_no_afecta_score(db):
    """Reporte validado pero a mas de 150m de distancia no debe afectar el score."""
    # Coordenada a ~1000m de la calle de prueba (suficientemente lejos)
    insertar_reporte_validado(db, lat=0.009, lon=0.0, incident_type="robo", severity="high")

    service = ScoreCalculatorService(db=db)
    service.calculate_all_scores()

    _, _, report_score, _ = obtener_score(db, 8000001)
    assert report_score == 0.0, (
        f"Un reporte fuera del radio de {150}m no deberia afectar el score. "
        f"report_score fue {report_score}"
    )
