import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime

from app.models.risk_score import RiskScore
from app.core.constants import (
    WEIGHT_DISTRICT, WEIGHT_CONTEXT, WEIGHT_REPORT,
    SCORE_NEUTRO,
    CONTEXT_WEIGHT_LIGHTING, CONTEXT_WEIGHT_POLICE,
    CONTEXT_WEIGHT_ROAD_TYPE, CONTEXT_WEIGHT_CAMERAS, CONTEXT_WEIGHT_COMMERCE,
    HIGHWAY_RISK, HIGHWAY_RISK_DEFAULT,
)


class ScoreCalculatorService:
    """
    Calcula el score compuesto de riesgo para cada segmento de calle.

    Fórmula (SAF-43):
        composite_score = w_d * district_score + w_c * context_score + w_r * report_score

    Por ahora solo están activas las capas 1 y 2 (w_r = 0.0).
    La capa 3 (reportes) se activa en el Sprint 6 (RF-18).
    """

    def __init__(self, db: Session):
        self.db = db

    def calculate_all_scores(self) -> int:
        """
        Orquesta el cálculo completo.
        Retorna cuántos segmentos fueron procesados.
        """
        print("Cargando segmentos de la BD...")
        df = self._cargar_segmentos()

        if df.empty:
            print("No hay segmentos en la BD. Ejecuta primero la ingesta del grafo.")
            return 0

        print(f"  -> {len(df)} segmentos encontrados")

        # --- Capa 1: score distrital ---
        print("Calculando district_score...")
        df = self._agregar_district_score(df)

        # --- Capa 2: score de contexto urbano ---
        print("Calculando context_score...")
        df = self._agregar_context_score(df)

        # --- Fórmula compuesta ---
        df["composite_score"] = (
            WEIGHT_DISTRICT * df["district_score"]
            + WEIGHT_CONTEXT  * df["context_score"]
            + WEIGHT_REPORT   * 0.0
        ).clip(0.0, 1.0).round(4)

        # --- Guardar en risk_scores ---
        print("Guardando scores en la BD...")
        self._guardar_scores(df)

        print(f"  -> {len(df)} scores guardados")
        return len(df)

    # ------------------------------------------------------------------
    # Carga base
    # ------------------------------------------------------------------

    def _cargar_segmentos(self) -> pd.DataFrame:
        """Trae id, tipo de vía, ubigeo y longitud de todos los segmentos."""
        sql = text("""
            SELECT id, highway_type, district_ubigeo, length_m
            FROM street_segments
        """)
        rows = self.db.execute(sql).fetchall()
        return pd.DataFrame(rows, columns=["id", "highway_type", "district_ubigeo", "length_m"])

    # ------------------------------------------------------------------
    # Capa 1: district_score
    # ------------------------------------------------------------------

    def _agregar_district_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Hace un join con district_crime_stats para traer la tasa normalizada.
        Si el segmento no tiene ubigeo o el distrito no tiene datos, usa SCORE_NEUTRO.
        """
        sql = text("SELECT district_ubigeo, weighted_crime_rate FROM district_crime_stats")
        rows = self.db.execute(sql).fetchall()
        df_rates = pd.DataFrame(rows, columns=["district_ubigeo", "weighted_crime_rate"])

        df = df.merge(df_rates, on="district_ubigeo", how="left")
        df["district_score"] = df["weighted_crime_rate"].fillna(SCORE_NEUTRO)
        return df

    # ------------------------------------------------------------------
    # Capa 2: context_score (5 factores según SAF-16)
    # ------------------------------------------------------------------

    def _agregar_context_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcula los 5 factores y los combina con sus pesos."""

        # Factor 3: tipo de vía (siempre disponible, no necesita query extra)
        df["r_road"] = df["highway_type"].map(HIGHWAY_RISK).fillna(HIGHWAY_RISK_DEFAULT)

        # Factor 2: presencia policial
        print("  Consultando distancias a comisarías (ST_DWithin)...")
        df_police = self._query_distancia_policia()
        df = df.merge(df_police, on="id", how="left")
        df["dist_policia"] = df["dist_policia"].fillna(9999.0)
        df["r_police"] = df["dist_policia"].apply(self._factor_policia)

        # Factor 4: cámaras y bancos (radio 150m)
        print("  Contando cámaras cercanas (ST_DWithin 150m)...")
        df_cameras = self._query_contar_pois("surveillance_camera", 150)
        df = df.merge(df_cameras, on="id", how="left")
        df["count_cameras"] = df["count_cameras"].fillna(0)
        df["r_cameras"] = (1 - (df["count_cameras"] / 2).clip(0, 1))

        # Factor 5: comercio (radio 100m)
        # Nota: los POIs de comercio (shop=*) no se ingestaron aún en esta versión.
        # Se usa SCORE_NEUTRO hasta que se carguen esos datos.
        df["r_commerce"] = SCORE_NEUTRO

        # Factor 1: iluminación (street_lamp, radio 50m)
        # Nota: tampoco se ingestaron aún. Se usa SCORE_NEUTRO.
        df["r_lighting"] = SCORE_NEUTRO

        # Suma ponderada de los 5 factores
        df["context_score"] = (
            CONTEXT_WEIGHT_LIGHTING  * df["r_lighting"]
            + CONTEXT_WEIGHT_POLICE    * df["r_police"]
            + CONTEXT_WEIGHT_ROAD_TYPE * df["r_road"]
            + CONTEXT_WEIGHT_CAMERAS   * df["r_cameras"]
            + CONTEXT_WEIGHT_COMMERCE  * df["r_commerce"]
        ).clip(0.0, 1.0).round(4)

        return df

    def _factor_policia(self, distancia_m: float) -> float:
        """Convierte distancia a comisaría en riesgo (SAF-16, factor 2)."""
        if distancia_m <= 300:
            return 0.0   # p_police = 1.0 -> r = 0
        elif distancia_m <= 600:
            return 0.5   # p_police = 0.5 -> r = 0.5
        else:
            return 1.0   # p_police = 0.0 -> r = 1.0

    def _query_distancia_policia(self) -> pd.DataFrame:
        """
        Para cada segmento, obtiene la distancia al POI de tipo police_station
        más cercano dentro de 700m (un poco más que el umbral de 600m del doc).
        Usa ::geography para que ST_Distance devuelva metros reales.
        """
        sql = text("""
            SELECT
                s.id,
                MIN(ST_Distance(
                    s.geometry::geography,
                    p.geometry::geography
                )) AS dist_policia
            FROM street_segments s
            LEFT JOIN urban_pois p
                ON p.poi_type = 'police_station'
                AND ST_DWithin(
                    s.geometry::geography,
                    p.geometry::geography,
                    700
                )
            GROUP BY s.id
        """)
        rows = self.db.execute(sql).fetchall()
        return pd.DataFrame(rows, columns=["id", "dist_policia"])

    def _query_contar_pois(self, poi_type: str, radio_m: int) -> pd.DataFrame:
        """
        Cuenta cuántos POIs de un tipo dado hay dentro del radio especificado
        de cada segmento. Usa ST_DWithin con geografía para metros reales.
        """
        sql = text("""
            SELECT
                s.id,
                COUNT(p.id) AS count_cameras
            FROM street_segments s
            LEFT JOIN urban_pois p
                ON p.poi_type = :poi_type
                AND ST_DWithin(
                    s.geometry::geography,
                    p.geometry::geography,
                    :radio
                )
            GROUP BY s.id
        """)
        rows = self.db.execute(sql, {"poi_type": poi_type, "radio": radio_m}).fetchall()
        return pd.DataFrame(rows, columns=["id", "count_cameras"])

    # ------------------------------------------------------------------
    # Persistencia
    # ------------------------------------------------------------------

    def _guardar_scores(self, df: pd.DataFrame):
        """
        Limpia la tabla risk_scores y vuelve a insertar todos los scores.
        Mismo patrón que CrimeAnalyticsService.update_stats_table().
        """
        self.db.query(RiskScore).delete()

        ahora = datetime.utcnow()
        for _, row in df.iterrows():
            score = RiskScore(
                segment_id=int(row["id"]),
                district_score=float(row["district_score"]),
                context_score=float(row["context_score"]),
                report_score=0.0,
                composite_score=float(row["composite_score"]),
                last_updated=ahora,
            )
            self.db.add(score)

        self.db.commit()

    # ------------------------------------------------------------------
    # Utilidad: categoría del score (SAF-44)
    # ------------------------------------------------------------------

    def get_categoria(self, security_score: int) -> str:
        """
        Convierte el security_score (0-100) a categoría de texto.
        security_score = round(100 * (1 - risk_route))
        """
        from app.core.constants import CATEGORIA_SEGURA, CATEGORIA_MODERADA
        if security_score >= CATEGORIA_SEGURA:
            return "Segura"
        elif security_score >= CATEGORIA_MODERADA:
            return "Moderada"
        else:
            return "Riesgosa"
