import logging

from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)


class SegmentDistrictService:
    """
    Servicio que asigna el district_ubigeo a cada segmento de calle usando la función espacial ST_Within de PostGIS.
    """
    def __init__(self, db: Session):
        self.db = db

    def assign_districts_to_segments(self) -> int:
        logger.info("Asignando distritos a segmentos via ST_Within...")

        missing_count = self.db.execute(
            text("SELECT COUNT(*) FROM street_segments WHERE district_ubigeo IS NULL")
        ).scalar()

        logger.info(f"Segmentos sin distrito: {missing_count}")

        if missing_count == 0:
            logger.info("Todos los segmentos ya tienen distrito asignado.")
            return 0

        update_query = text("""
            UPDATE street_segments AS seg
            SET district_ubigeo = d.ubigeo
            FROM districts AS d
            WHERE seg.district_ubigeo IS NULL
              AND ST_Within(
                  ST_Centroid(seg.geometry),
                  d.geometry
              )
        """)

        result = self.db.execute(update_query)
        self.db.commit()

        updated = result.rowcount
        logger.info(f"{updated} segmentos actualizados con su distrito")

        unassigned = self.db.execute(
            text("SELECT COUNT(*) FROM street_segments WHERE district_ubigeo IS NULL")
        ).scalar()

        if unassigned > 0:
            logger.warning(
                f"{unassigned} segmentos siguen sin distrito "
                "(probablemente en los bordes o fuera de los polígonos)"
            )

        return updated

    def get_summary(self) -> list:
        query = text("""
            SELECT d.name, d.ubigeo, COUNT(seg.id) AS total_segmentos
            FROM districts d
            LEFT JOIN street_segments seg ON seg.district_ubigeo = d.ubigeo
            GROUP BY d.name, d.ubigeo
            ORDER BY total_segmentos DESC
        """)

        rows = self.db.execute(query).fetchall()
        return rows
