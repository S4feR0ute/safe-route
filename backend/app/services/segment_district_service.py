from sqlalchemy.orm import Session
from sqlalchemy import text


class SegmentDistrictService:
    """
    Servicio que asigna el district_ubigeo a cada segmento de calle usando la función espacial ST_Within de PostGIS.
    """
    def __init__(self, db: Session):
        self.db = db

    def assign_districts_to_segments(self) -> int:
        print("Asignando distritos a segmentos via ST_Within...")

        count_sin_distrito = self.db.execute(
            text("SELECT COUNT(*) FROM street_segments WHERE district_ubigeo IS NULL")
        ).scalar()

        print(f"  Segmentos sin distrito: {count_sin_distrito}")

        if count_sin_distrito == 0:
            print("  -> Todos los segmentos ya tienen distrito asignado.")
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
        print(f"  -> {updated} segmentos actualizados con su distrito")

        sin_asignar = self.db.execute(
            text("SELECT COUNT(*) FROM street_segments WHERE district_ubigeo IS NULL")
        ).scalar()

        if sin_asignar > 0:
            print(f"  Advertencia: {sin_asignar} segmentos siguen sin distrito")
            print("  (probablemente están en los bordes o fuera de los polígonos)")

        return updated

    def get_resumen(self) -> list:
        query = text("""
            SELECT d.name, d.ubigeo, COUNT(seg.id) AS total_segmentos
            FROM districts d
            LEFT JOIN street_segments seg ON seg.district_ubigeo = d.ubigeo
            GROUP BY d.name, d.ubigeo
            ORDER BY total_segmentos DESC
        """)

        rows = self.db.execute(query).fetchall()
        return rows
