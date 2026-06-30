import pytest
from sqlalchemy import text

from app.db.session import SessionLocal
from app.models.street_network import StreetSegment, StreetNode
from app.models.risk_score import RiskScore
from app.services.score_calculator_service import ScoreCalculatorService


@pytest.fixture(scope="module")
def db():
    """Sesion de base de datos compartida para todos los tests de este archivo."""
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="module", autouse=True)
def datos_sinteticos(db):
    """Inserta las 5 calles de prueba (TC1-TC5) antes de los tests y las borra al final."""
    setup_sql = """
    INSERT INTO district_crime_stats (district_ubigeo, district_name, total_incidents_count, violent_incidents_count, weighted_crime_rate) VALUES
    ('999901', 'Distrito Sintetico Alto Riesgo', 100, 80, 0.90),
    ('999902', 'Distrito Sintetico Bajo Riesgo', 100, 5, 0.10);

    INSERT INTO street_nodes (node_id, geometry, lat, lon) VALUES
    (9000001, ST_SetSRID(ST_MakePoint(0, 0), 4326), 0, 0),
    (9000002, ST_SetSRID(ST_MakePoint(0, 0.001), 4326), 0.001, 0),
    (9000003, ST_SetSRID(ST_MakePoint(0, 0.01), 4326), 0.01, 0),
    (9000004, ST_SetSRID(ST_MakePoint(0, 0.011), 4326), 0.011, 0),
    (9000005, ST_SetSRID(ST_MakePoint(0, 0.02), 4326), 0.02, 0),
    (9000006, ST_SetSRID(ST_MakePoint(0, 0.021), 4326), 0.021, 0),
    (9000007, ST_SetSRID(ST_MakePoint(0, 0.03), 4326), 0.03, 0),
    (9000008, ST_SetSRID(ST_MakePoint(0, 0.031), 4326), 0.031, 0),
    (9000009, ST_SetSRID(ST_MakePoint(0, 0.04), 4326), 0.04, 0),
    (9000010, ST_SetSRID(ST_MakePoint(0, 0.041), 4326), 0.041, 0);

    INSERT INTO street_segments (id, osm_way_id, geometry, name, length_m, highway_type, oneway, source_node_id, target_node_id, district_ubigeo) VALUES
    (9000001, 9000001, ST_SetSRID(ST_MakeLine(ST_MakePoint(0,0), ST_MakePoint(0,0.001)), 4326), 'TC1', 111.0, 'path', false, 9000001, 9000002, '999901'),
    (9000002, 9000002, ST_SetSRID(ST_MakeLine(ST_MakePoint(0,0.01), ST_MakePoint(0,0.011)), 4326), 'TC2', 111.0, 'primary', false, 9000003, 9000004, '999902'),
    (9000003, 9000003, ST_SetSRID(ST_MakeLine(ST_MakePoint(0,0.02), ST_MakePoint(0,0.021)), 4326), 'TC3', 111.0, 'residential', false, 9000005, 9000006, '999903'),
    (9000004, 9000004, ST_SetSRID(ST_MakeLine(ST_MakePoint(0,0.03), ST_MakePoint(0,0.031)), 4326), 'TC4', 111.0, 'residential', false, 9000007, 9000008, '999904'),
    (9000005, 9000005, ST_SetSRID(ST_MakeLine(ST_MakePoint(0,0.04), ST_MakePoint(0,0.041)), 4326), 'TC5', 111.0, 'residential', false, 9000009, 9000010, '999905');

    INSERT INTO urban_pois (osm_id, poi_type, name, geometry) VALUES
    ('test_police_tc2', 'police_station', 'Comisaria TC2', ST_SetSRID(ST_MakePoint(0, 0.0105), 4326)),
    ('test_camera_tc2_1', 'surveillance_camera', 'Camara TC2-1', ST_SetSRID(ST_MakePoint(0, 0.0102), 4326)),
    ('test_camera_tc2_2', 'surveillance_camera', 'Camara TC2-2', ST_SetSRID(ST_MakePoint(0, 0.0108), 4326)),
    ('test_police_tc4', 'police_station', 'Comisaria TC4', ST_SetSRID(ST_MakePoint(0.0036, 0.0305), 4326)),
    ('test_camera_tc5', 'surveillance_camera', 'Camara TC5', ST_SetSRID(ST_MakePoint(0, 0.0405), 4326));
    """

    cleanup_sql = """
    DELETE FROM risk_scores WHERE segment_id IN (9000001,9000002,9000003,9000004,9000005);
    DELETE FROM street_segments WHERE id IN (9000001,9000002,9000003,9000004,9000005);
    DELETE FROM street_nodes WHERE node_id IN (9000001,9000002,9000003,9000004,9000005,9000006,9000007,9000008,9000009,9000010);
    DELETE FROM district_crime_stats WHERE district_ubigeo IN ('999901','999902');
    DELETE FROM urban_pois WHERE osm_id IN ('test_police_tc2','test_camera_tc2_1','test_camera_tc2_2','test_police_tc4','test_camera_tc5');
    """

    db.execute(text(cleanup_sql))
    db.commit()

    db.execute(text(setup_sql))
    db.commit()

    service = ScoreCalculatorService(db=db)
    service.calculate_all_scores()

    yield

    db.execute(text(cleanup_sql))
    db.commit()


def obtener_score(db, segment_id):
    sql = text("""
        SELECT district_score, context_score, composite_score
        FROM risk_scores WHERE segment_id = :sid
    """)
    row = db.execute(sql, {"sid": segment_id}).fetchone()
    assert row is not None, f"No se encontro score para el segmento {segment_id}"
    return row


def test_cp_b01_distrito_alto_riesgo(db):
    """TC1: sendero (path) en distrito de alta criminalidad, sin infraestructura cercana."""
    district_score, context_score, composite_score = obtener_score(db, 9000001)
    assert district_score == pytest.approx(0.90)
    assert context_score == pytest.approx(0.85)
    assert composite_score == pytest.approx(0.885)


def test_cp_b02_distrito_bajo_riesgo(db):
    """TC2: avenida principal (primary) en distrito seguro, con comisaria cerca y 2 camaras."""
    district_score, context_score, composite_score = obtener_score(db, 9000002)
    assert district_score == pytest.approx(0.10)
    assert context_score == pytest.approx(0.0727, abs=0.001)
    assert composite_score == pytest.approx(0.0918, abs=0.001)


def test_cp_b03_distrito_sin_datos_usa_valor_neutro(db):
    """TC3: distrito sin datos de criminalidad debe usar SCORE_NEUTRO (0.5)."""
    district_score, context_score, composite_score = obtener_score(db, 9000003)
    assert district_score == pytest.approx(0.5)
    assert context_score == pytest.approx(0.45)
    assert composite_score == pytest.approx(0.485)


def test_cp_b04_policia_distancia_intermedia(db):
    """TC4: comisaria a distancia intermedia (~404m) debe dar r_police = 0.5."""
    district_score, context_score, composite_score = obtener_score(db, 9000004)
    assert context_score == pytest.approx(0.475)
    assert composite_score == pytest.approx(0.4925)


def test_cp_b05_una_camara_cercana(db):
    """TC5: exactamente 1 camara cercana debe dar r_cameras = 0.5."""
    district_score, context_score, composite_score = obtener_score(db, 9000005)
    assert context_score == pytest.approx(0.4714, abs=0.001)
    assert composite_score == pytest.approx(0.4914, abs=0.001)
