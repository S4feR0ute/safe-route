import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session as SQLASession

from app.db.session import engine
from app.models.crime_raw import CrimeRawData
from app.models.crime_type_weight import CrimeTypeWeight
from app.models.crime_stats import DistrictCrimeStats
from app.services.crime_analytics_service import CrimeAnalyticsService


@pytest.fixture
def db(monkeypatch):
    """
    Abrimos UNA sola conexion real a la BD y una transaccion sobre ella.
    La sesion se ata a esa misma conexion (en vez de al motor general),
    para que TODO -- insertar datos de prueba y que el servicio los lea --
    pase por el mismo canal y dentro de la misma transaccion.
    El commit() interno se desactiva, y al final se hace rollback() real
    sobre la conexion: los datos reales de produccion quedan intactos.
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
    Limpia (solo dentro de esta transaccion que nunca se confirma) y crea
    4 distritos de prueba con tipos de delito conocidos:
      - Distrito A: ROBO (peso 1.0) x50  -> el de mayor riesgo
      - Distrito B: HURTO (peso 0.5) x20 -> riesgo intermedio
      - Distrito C: OTRO (sin peso definido) x40 -> prueba el peso por defecto (0.05)
      - Distrito D: ROBO (peso 1.0) x1   -> ancla de riesgo minimo
    """
    db.query(DistrictCrimeStats).delete()
    db.query(CrimeRawData).delete()
    db.query(CrimeTypeWeight).delete()

    db.add_all([
        CrimeTypeWeight(subtype_name="ROBO", danger_weight=1.0, is_street_crime=True),
        CrimeTypeWeight(subtype_name="HURTO", danger_weight=0.5, is_street_crime=True),
    ])

    db.add_all([
        CrimeRawData(district_ubigeo="999801", district_name="Distrito A",
                      period="2026", crime_type="ROBO", incident_count=50),
        CrimeRawData(district_ubigeo="999802", district_name="Distrito B",
                      period="2026", crime_type="HURTO", incident_count=20),
        CrimeRawData(district_ubigeo="999803", district_name="Distrito C",
                      period="2026", crime_type="OTRO", incident_count=40),
        CrimeRawData(district_ubigeo="999804", district_name="Distrito D",
                      period="2026", crime_type="ROBO", incident_count=1),
    ])
    db.flush()


def obtener_stats(db, ubigeo):
    sql = text("""
        SELECT total_incidents_count, violent_incidents_count, weighted_crime_rate
        FROM district_crime_stats WHERE district_ubigeo = :ubigeo
    """)
    row = db.execute(sql, {"ubigeo": ubigeo}).fetchone()
    assert row is not None, f"No se encontraron stats para el distrito {ubigeo}"
    return row


def test_pesos_se_cargan_desde_la_bd_no_desde_el_fallback(db):
    service = CrimeAnalyticsService(db=db)
    pesos = service._cargar_pesos()
    assert pesos == {"ROBO": 1.0, "HURTO": 0.5}


def test_distrito_mas_violento_obtiene_el_riesgo_maximo(db):
    service = CrimeAnalyticsService(db=db)
    service.process_crime_metrics()

    total, violentos, rate = obtener_stats(db, "999801")
    assert total == 50
    assert violentos == 50
    assert rate == pytest.approx(1.0)


def test_distrito_con_menor_peso_obtiene_riesgo_intermedio(db):
    service = CrimeAnalyticsService(db=db)
    service.process_crime_metrics()

    total, violentos, rate = obtener_stats(db, "999802")
    assert total == 20
    assert violentos == 20
    assert rate == pytest.approx(0.356161, abs=0.0001)


def test_tipo_de_delito_desconocido_usa_peso_por_defecto_005(db):
    """
    'OTRO' no esta registrado en crime_types_weights. El codigo debe
    asignarle el peso por defecto 0.05 (fillna(0.05)), no tratarlo como
    0 (lo que rompería el orden esperado frente al Distrito D) ni como
    un delito violento.
    """
    service = CrimeAnalyticsService(db=db)
    service.process_crime_metrics()

    total, violentos, rate = obtener_stats(db, "999803")
    assert total == 40
    assert violentos == 0  # 'OTRO' no cuenta como delito violento
    assert rate == pytest.approx(0.068227, abs=0.0001)


def test_distrito_con_menos_incidentes_obtiene_el_riesgo_minimo(db):
    service = CrimeAnalyticsService(db=db)
    service.process_crime_metrics()

    total, violentos, rate = obtener_stats(db, "999804")
    assert total == 1
    assert violentos == 1
    assert rate == pytest.approx(0.0)


def test_no_afecta_datos_reales_de_otros_distritos(db):
    """
    Verifica que esta prueba realmente vive solo dentro de la transaccion
    de test: los distritos reales de Lima (ej. San Isidro) no deben verse
    afectados ni durante la ejecucion de este archivo.
    """
    service = CrimeAnalyticsService(db=db)
    service.process_crime_metrics()

    sql = text("SELECT COUNT(*) FROM district_crime_stats")
    total_distritos = db.execute(sql).scalar()
    assert total_distritos == 4  # solo nuestros 4 distritos sinteticos, dentro de esta transaccion
