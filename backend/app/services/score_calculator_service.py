import logging
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime

from app.models.risk_score import RiskScore

logger = logging.getLogger(__name__)
from app.core.constants import (
    WEIGHT_DISTRICT, WEIGHT_CONTEXT, WEIGHT_REPORT,
    SCORE_NEUTRO,
    CONTEXT_WEIGHT_LIGHTING, CONTEXT_WEIGHT_POLICE,
    CONTEXT_WEIGHT_ROAD_TYPE, CONTEXT_WEIGHT_CAMERAS, CONTEXT_WEIGHT_COMMERCE,
    HIGHWAY_RISK, HIGHWAY_RISK_DEFAULT,
    CATEGORIA_SEGURA, CATEGORIA_MODERADA
)


class ScoreCalculatorService:
    """Calcula el score compuesto de riesgo para cada segmento de calle"""

    def __init__(self, db: Session):
        self.db = db

    def calculate_all_scores(self) -> int:
        logger.info("Cargando segmentos de la BD")
        df = self._cargar_segmentos()

        if df.empty:
            logger.warning("No hay segmentos en la BD")
            return 0

        logger.info(f"{len(df)} segmentos encontrados")

        # --- Capa 1: score distrital ---
        logger.info("Calculando district_score")
        df = self._agregar_district_score(df)

        # --- Capa 2: score de contexto urbano ---
        logger.info("Calculando context_score")
        df = self._agregar_context_score(df)

        # --- Fórmula compuesta ---
        df["composite_score"] = (
            WEIGHT_DISTRICT * df["district_score"]
            + WEIGHT_CONTEXT  * df["context_score"]
            + WEIGHT_REPORT   * 0.0
        ).clip(0.0, 1.0).round(4)

        # --- Guardar en risk_scores ---
        logger.info("Guardando scores en la BD")
        self._guardar_scores(df)

        logger.info(f"{len(df)} scores guardados")
        return len(df)

    def _cargar_segmentos(self) -> pd.DataFrame:
        """Trae id, tipo de vía, ubigeo y longitud de todos los segmentos."""
        sql = text("""
            SELECT id, highway_type, district_ubigeo, length_m
            FROM street_segments
        """)
        rows = self.db.execute(sql).fetchall()
        return pd.DataFrame(rows, columns=["id", "highway_type", "district_ubigeo", "length_m"])

    def _agregar_district_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Hace un join con district_crime_stats para traer la tasa normalizada.
        Si el segmento no tiene ubigeo o el distrito no tiene datos, usa SCORE_NEUTRO.
        """
        query = text("SELECT district_ubigeo, weighted_crime_rate FROM district_crime_stats")
        rows = self.db.execute(query).fetchall()
        df_rates = pd.DataFrame(rows, columns=["district_ubigeo", "weighted_crime_rate"])

        df = df.merge(df_rates, on="district_ubigeo", how="left")
        df["district_score"] = df["weighted_crime_rate"].fillna(SCORE_NEUTRO)
        return df

    def _agregar_context_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula los factores y los combina con pesos redistribuidos. 
        Si un factor no tiene datos (usa SCORE_NEUTRO), su peso se redistribuye
        """
        # Tipo de vía
        df["r_road"] = df["highway_type"].map(HIGHWAY_RISK).fillna(HIGHWAY_RISK_DEFAULT)
        df["has_road"] = True

        # Presencia policial
        logger.debug("Consultando distancias a comisarías")
        df_police = self._query_distancia_policia()
        df = df.merge(df_police, on="id", how="left")
        df["dist_policia"] = df["dist_policia"].fillna(9999.0)
        df["r_police"] = df["dist_policia"].apply(self._factor_policia)
        df["has_police"] = df["dist_policia"] < 700  # Tiene dato si está dentro del radio

        # Vigilancia - cámaras (radio 150m)
        logger.debug("Contando cámaras de vigilancia cercanas")
        df_cameras = self._query_contar_pois("surveillance_camera", 150)
        df = df.merge(df_cameras, on="id", how="left")
        df["count_cameras"] = df["count_cameras"].fillna(0)
        df["has_cameras"] = df["count_cameras"] > 0

        # Vigilancia - bancos (también 150m, contribuyen a seguridad)
        logger.debug("Contando bancos cercanos")
        df_banks = self._query_contar_pois("bank", 150)
        df = df.merge(df_banks, on="id", how="left", suffixes=("", "_bank"))
        df["count_banks"] = df["count_cameras_bank"].fillna(0)
        df["count_cameras"] = df["count_cameras"] + df["count_banks"]
        df["r_cameras"] = (1 - ((df["count_cameras"] / 2).clip(0, 1)))
        df.drop(columns=["count_banks", "count_cameras_bank"], inplace=True)

        # Iluminación - postes de luz (radio 50m)
        logger.debug("Contando postes de luz cercanos")
        df_lighting = self._query_contar_pois("street_lamp", 50)
        df = df.merge(df_lighting, on="id", how="left", suffixes=("", "_light"))
        df["count_lighting"] = df["count_cameras_light"].fillna(0)
        # Densidad de iluminación: (1 - min(count/5, 1.0)) - normalizamos por 5 lámparas
        df["r_lighting"] = (1 - (df["count_lighting"] / 5).clip(0, 1))
        df["has_lighting"] = df["count_lighting"] > 0
        df.drop(columns=["count_cameras_light"], inplace=True)

        # Comercio (radio 100m)
        logger.debug("Contando POIs comerciales cercanos")
        df_shops = self._query_contar_pois("shop", 100)
        df = df.merge(df_shops, on="id", how="left", suffixes=("", "_shop"))
        df["count_shops"] = df["count_cameras_shop"].fillna(0)

        df_restaurants = self._query_contar_pois("restaurant", 100)
        df = df.merge(df_restaurants, on="id", how="left", suffixes=("", "_rest"))
        df["count_restaurants"] = df["count_cameras_rest"].fillna(0)

        df_pharmacy = self._query_contar_pois("pharmacy", 100)
        df = df.merge(df_pharmacy, on="id", how="left", suffixes=("", "_pharm"))
        df["count_pharmacy"] = df["count_cameras_pharm"].fillna(0)

        df_fuel = self._query_contar_pois("fuel", 100)
        df = df.merge(df_fuel, on="id", how="left", suffixes=("", "_fuel"))
        df["count_fuel"] = df["count_cameras_fuel"].fillna(0)

        df_market = self._query_contar_pois("marketplace", 100)
        df = df.merge(df_market, on="id", how="left", suffixes=("", "_market"))
        df["count_market"] = df["count_cameras_market"].fillna(0)

        # Total de POIs comerciales
        df["count_commerce"] = (
            df["count_shops"] + df["count_restaurants"] +
            df["count_pharmacy"] + df["count_fuel"] + df["count_market"]
        )

        # Normalización: min(count/10, 1.0) - esperamos ~10 POIs de actividad comercial
        df["r_commerce"] = (1 - (df["count_commerce"] / 10).clip(0, 1))
        df["has_commerce"] = df["count_commerce"] > 0

        # Limpiar columnas temporales
        df.drop(columns=[
            "count_cameras_shop", "count_shops",
            "count_cameras_rest", "count_restaurants",
            "count_cameras_pharm", "count_pharmacy",
            "count_cameras_fuel", "count_fuel",
            "count_cameras_market", "count_market",
            "count_commerce", "count_cameras"
        ], inplace=True)

        # --- Calcular pesos redistribuidos  ---s
        def calcular_context_score_fila(fila):
            factores = [
                ("lighting", fila["r_lighting"], CONTEXT_WEIGHT_LIGHTING, fila["has_lighting"]),
                ("police", fila["r_police"], CONTEXT_WEIGHT_POLICE, fila["has_police"]),
                ("road", fila["r_road"], CONTEXT_WEIGHT_ROAD_TYPE, fila["has_road"]),
                ("cameras", fila["r_cameras"], CONTEXT_WEIGHT_CAMERAS, fila["has_cameras"]),
                ("commerce", fila["r_commerce"], CONTEXT_WEIGHT_COMMERCE, fila["has_commerce"]),
            ]

            # Suma de pesos para factores con datos
            peso_total_activos = sum(peso for _, _, peso, tiene_dato in factores if tiene_dato)

            # Si no hay factores con datos, devolver SCORE_NEUTRO
            if peso_total_activos == 0:
                return SCORE_NEUTRO

            # Sumar valor × peso redistribuido
            score = 0.0
            for nombre, valor, peso_original, tiene_dato in factores:
                if tiene_dato:
                    peso_redistribuido = peso_original / peso_total_activos
                    score += valor * peso_redistribuido

            return score

        df["context_score"] = df.apply(calcular_context_score_fila, axis=1).clip(0.0, 1.0).round(4)

        # Limpiar columnas temporales
        df.drop(columns=["has_lighting", "has_police", "has_road", "has_cameras", "has_commerce"], inplace=True)

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

    def _guardar_scores(self, df: pd.DataFrame):
        self.db.query(RiskScore).delete()

        ahora = datetime.utcnow()
        scores_data = [
            {
                "segment_id": int(row["id"]),
                "district_score": float(row["district_score"]),
                "context_score": float(row["context_score"]),
                "report_score": 0.0,
                "composite_score": float(row["composite_score"]),
                "last_updated": ahora,
            }
            for _, row in df.iterrows()
        ]

        self.db.bulk_insert_mappings(RiskScore, scores_data)
        self.db.commit()
        logger.info(f"Insertados {len(scores_data)} scores vía bulk_insert")

    def get_categoria(self, security_score: int) -> str:
        if security_score >= CATEGORIA_SEGURA:
            return "Segura"
        elif security_score >= CATEGORIA_MODERADA:
            return "Moderada"
        else:
            return "Riesgosa"
