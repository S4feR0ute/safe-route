import logging
import math
import networkx as nx
from sqlalchemy.orm import Session

from app.interfaces.street_graph_interface import IStreetGraphDAO
from app.repositories.risk_score_repository import RiskScoreRepository
from app.core.constants import (
    ALPHA_RISK,
    NEUTRAL_SCORE,
    CATEGORY_SAFE_THRESHOLD,
    CATEGORY_MODERATE_THRESHOLD,
    RISK_LOW,
    RISK_MEDIUM,
    MAX_RED_FRACTION,
    WALKING_SPEED_MPM,
)
from app.core.exceptions import EmptyGraphError, NoRouteError, NodeNotFoundError
from app.utils.geo import haversine_m

logger = logging.getLogger(__name__)


class RoutingService:
    """
    Servicio de ruteo usando algoritmo de Dijkstra ponderado.
    """
    def __init__(self, db: Session, graph_dao: IStreetGraphDAO, score_repo: RiskScoreRepository):
        self.db = db
        self.graph_dao = graph_dao
        self.score_repo = score_repo

    def calculate_routes(self, origin_lat: float, origin_lon: float, dest_lat: float, dest_lon: float) -> dict:
        """Calcula la ruta segura y la ruta corta entre dos coordenadas, con sus métricas y GeoJSON."""
        logger.info("Cargando grafo desde la BD...")
        graph = self._load_graph_with_scores()

        if graph.number_of_nodes() == 0:
            raise EmptyGraphError("El grafo está vacío. Ejecuta primero ingest_street_graph.py")

        logger.info("Buscando nodos más cercanos al origen y destino...")
        origin_node = self._find_nearest_node(graph, origin_lat, origin_lon)
        dest_node = self._find_nearest_node(graph, dest_lat, dest_lon)
        logger.info(f"Nodo origen: {origin_node} | Nodo destino: {dest_node}")

        logger.info("Calculando ruta segura (Dijkstra ponderado por riesgo)...")
        try:
            safe_path = nx.dijkstra_path(graph, origin_node, dest_node, weight="cost")
        except nx.NetworkXNoPath:
            raise NoRouteError("No existe ruta entre los puntos seleccionados")
        except nx.NodeNotFound as e:
            raise NodeNotFoundError(f"Nodo no encontrado en el grafo: {e}")

        logger.info("Calculando ruta corta (Dijkstra por longitud)...")
        try:
            short_path = nx.dijkstra_path(graph, origin_node, dest_node, weight="length")
        except nx.NetworkXNoPath:
            short_path = safe_path

        safe_segments = self._extract_segments(graph, safe_path)
        short_segments = self._extract_segments(graph, short_path)

        safe_score = self._compute_security_score(safe_segments)
        short_score = self._compute_security_score(short_segments)

        return {
            "safe_route": {
                "nodes": safe_path,
                "segments": safe_segments,
                "total_length_m": round(sum(s["length_m"] for s in safe_segments), 2),
                "security_score": safe_score,
                "category": self._get_category(safe_score, safe_segments),
            },
            "short_route": {
                "nodes": short_path,
                "segments": short_segments,
                "total_length_m": round(sum(s["length_m"] for s in short_segments), 2),
                "security_score": short_score,
                "category": self._get_category(short_score, short_segments),
            },
        }

    def build_route_response(self, result: dict, include_shortest: bool = True) -> dict:
        """Construye la respuesta del API a partir del resultado de calculate_routes."""
        safe_route = result["safe_route"]
        short_route = result["short_route"]

        response = {
            "safe_route": {
                "summary": self._build_summary(safe_route),
                "geojson": self._build_geojson(safe_route["segments"]),
            },
            "shortest_route": None,
            "comparison": None,
        }

        if include_shortest:
            response["shortest_route"] = {
                "summary": self._build_summary(short_route),
                "geojson": self._build_geojson(short_route["segments"]),
            }
            response["comparison"] = self._build_comparison(safe_route, short_route)

        return response

    def _load_graph_with_scores(self) -> nx.MultiDiGraph:
        """Carga de grafo y asigna costos ponderados por riesgo a cada arista."""
        graph = self.graph_dao.load_graph()
        scores_map = self._load_edge_scores()

        scored_edges = 0
        for u, v, _key, data in graph.edges(keys=True, data=True):
            length = data.get("length", 1.0) or 1.0
            composite = scores_map.get((u, v), NEUTRAL_SCORE)

            data["cost"] = length * (1 + ALPHA_RISK * composite)
            data["composite_score"] = composite

            if (u, v) in scores_map:
                scored_edges += 1

        logger.info(f"{scored_edges}/{graph.number_of_edges()} aristas con score asignado")
        return graph

    def _load_edge_scores(self) -> dict:
        """Carga scores desde el repository mapeados por nodos."""
        return self.score_repo.get_scores_mapped_by_nodes()

    def _find_nearest_node(self, graph: nx.MultiDiGraph, lat: float, lon: float) -> int:
        """Encuentra el nodo del grafo más cercano a las coordenadas dadas."""
        best_node = None
        best_dist = float("inf")

        for node_id, data in graph.nodes(data=True):
            # data["x"] = longitud, data["y"] = latitud (en grados)
            dist = haversine_m(lat, lon, data["y"], data["x"])
            if dist < best_dist:
                best_dist = dist
                best_node = node_id

        return best_node

    def _extract_segments(self, graph: nx.MultiDiGraph, path_nodes: list) -> list:
        """Extrae segmentos del path calculado por Dijkstra."""
        segments = []

        for i in range(len(path_nodes) - 1):
            u = path_nodes[i]
            v = path_nodes[i + 1]

            edges_dict = graph[u][v]

            if not edges_dict:
                continue

            selected_key = min(
                edges_dict.keys(),
                key=lambda k: edges_dict[k].get("cost", edges_dict[k].get("length", 1.0))
            )
            edge_data = edges_dict[selected_key]

            geom = edge_data.get("geometry")
            if geom:
                coords = list(geom.coords)
            else:
                coords = [
                    (graph.nodes[u]["x"], graph.nodes[u]["y"]),
                    (graph.nodes[v]["x"], graph.nodes[v]["y"]),
                ]

            segments.append({
                "source_node":     u,
                "target_node":     v,
                "edge_key":        selected_key,
                "name":            edge_data.get("name", "Sin nombre"),
                "length_m":        edge_data.get("length", 0.0) or 0.0,
                "composite_score": edge_data.get("composite_score", NEUTRAL_SCORE),
                "coordinates":     coords,
            })

        return segments

    def _compute_security_score(self, segments: list) -> int:
        """Calcula el security_score de una ruta como promedio ponderado por longitud de los segmentos."""
        if not segments:
            return 50

        total_length = sum(s["length_m"] for s in segments)
        weighted_sum = sum(s["length_m"] * s["composite_score"] for s in segments)

        if total_length == 0:
            return 50

        risk_route = weighted_sum / total_length
        return round(100 * (1 - risk_route))

    def _get_category(self, security_score: int, segments: list = None) -> str:
        """Determina categoría de la ruta con degradación."""
        if security_score >= CATEGORY_SAFE_THRESHOLD:
            base_category = "Segura"
        elif security_score >= CATEGORY_MODERATE_THRESHOLD:
            base_category = "Moderada"
        else:
            base_category = "Riesgosa"

        if base_category == "Segura" and segments:
            total_length = sum(s["length_m"] for s in segments)
            if total_length > 0:
                red_length = sum(
                    s["length_m"] for s in segments
                    if s.get("composite_score", NEUTRAL_SCORE) > RISK_MEDIUM
                )
                # Si > 10% de la longitud es roja, degradar a Moderada
                if red_length / total_length > MAX_RED_FRACTION:
                    return "Moderada"

        return base_category

    def _build_geojson(self, segments: list) -> dict:
        """Convierte la lista de segmentos en un GeoJSON FeatureCollection."""
        features = []
        for seg in segments:
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": seg["coordinates"],
                },
                "properties": {
                    "name":       seg["name"],
                    "length_m":   round(seg["length_m"], 2),
                    "risk_score": round(seg["composite_score"], 4),
                    "color":      self._color_for_score(seg["composite_score"]),
                },
            })
        return {"type": "FeatureCollection", "features": features}

    def _build_summary(self, route: dict) -> dict:
        """Arma el summary de una ruta con distancia, tiempo y score."""
        dist = route["total_length_m"]
        return {
            "distance_m":     round(dist, 2),
            "walk_time_min":  math.ceil(dist / WALKING_SPEED_MPM),
            "security_score": route["security_score"],
            "category":       route["category"],
        }

    def _build_comparison(self, safe_route: dict, short_route: dict) -> dict:
        """Calcula las diferencias entre la ruta segura y la corta."""
        extra_m = safe_route["total_length_m"] - short_route["total_length_m"]
        extra_min = math.ceil(abs(extra_m) / WALKING_SPEED_MPM)

        safe_risk = 1 - (safe_route["security_score"] / 100)
        short_risk = 1 - (short_route["security_score"] / 100)

        if short_risk > 0:
            reduction_pct = round(((short_risk - safe_risk) / short_risk) * 100, 1)
        else:
            reduction_pct = 0.0

        return {
            "extra_distance_m":   round(extra_m, 2),
            "extra_time_min":     extra_min,
            "risk_reduction_pct": reduction_pct,
        }

    @staticmethod
    def _color_for_score(composite_score: float) -> str:
        """Devuelve el color hex del segmento según su composite_score (SAF-44)."""
        if composite_score <= RISK_LOW:
            return "#2E7D32"   # verde
        elif composite_score <= RISK_MEDIUM:
            return "#F9A825"   # amarillo
        else:
            return "#C62828"   # rojo
