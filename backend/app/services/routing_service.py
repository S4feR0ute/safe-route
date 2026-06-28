import networkx as nx
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.interfaces.street_graph_interface import IStreetGraphDAO
from app.repositories.osmnx_street_graph_dao import OSMnxStreetGraphDAO
from app.repositories.risk_score_repository import RiskScoreRepository
from app.core.constants import (
    ALPHA_RISK,
    SCORE_NEUTRO,
    CATEGORIA_SEGURA,
    CATEGORIA_MODERADA,
    RIESGO_MEDIO,
    DEGRADACION_ROJO_MAX,
)


class RoutingService:
    """
    Servicio de ruteo usando algoritmo de Dijkstra ponderado.
    """
    def __init__(self, db: Session, graph_dao: IStreetGraphDAO = None):
        self.db = db
        self._graph_dao = graph_dao
        self._score_repo = RiskScoreRepository(db)

    def calcular_rutas(self, origen_lat: float, origen_lon: float, destino_lat: float, destino_lon: float) -> dict:
        print("Cargando grafo desde la BD...")
        graph = self._cargar_grafo_con_scores()

        if graph.number_of_nodes() == 0:
            raise ValueError("El grafo está vacío. Ejecuta primero ingest_street_graph.py")

        print("Buscando nodos más cercanos al origen y destino...")
        nodo_origen  = self._nodo_mas_cercano(graph, origen_lat, origen_lon)
        nodo_destino = self._nodo_mas_cercano(graph, destino_lat, destino_lon)
        print(f"  Nodo origen: {nodo_origen} | Nodo destino: {nodo_destino}")

        print("Calculando ruta segura (Dijkstra ponderado por riesgo)...")
        try:
            path_segura = nx.dijkstra_path(graph, nodo_origen, nodo_destino, weight="cost")
        except nx.NetworkXNoPath:
            raise ValueError("No existe ruta entre los puntos seleccionados")
        except nx.NodeNotFound as e:
            raise ValueError(f"Nodo no encontrado en el grafo: {e}")

        print("Calculando ruta corta (Dijkstra por longitud)...")
        try:
            path_corta = nx.dijkstra_path(graph, nodo_origen, nodo_destino, weight="length")
        except nx.NetworkXNoPath:
            path_corta = path_segura

        segmentos_segura = self._extraer_segmentos(graph, path_segura)
        segmentos_corta  = self._extraer_segmentos(graph, path_corta)

        score_segura = self._calcular_security_score(segmentos_segura)
        score_corta  = self._calcular_security_score(segmentos_corta)

        return {
            "ruta_segura": {
                "nodos": path_segura,
                "segmentos": segmentos_segura,
                "longitud_total_m": round(sum(s["length_m"] for s in segmentos_segura), 2),
                "security_score": score_segura,
                "categoria": self._get_categoria(score_segura, segmentos_segura),
            },
            "ruta_corta": {
                "nodos": path_corta,
                "segmentos": segmentos_corta,
                "longitud_total_m": round(sum(s["length_m"] for s in segmentos_corta), 2),
                "security_score": score_corta,
                "categoria": self._get_categoria(score_corta, segmentos_corta),
            },
        }

    def _cargar_grafo_con_scores(self) -> nx.MultiDiGraph:
        dao = self._graph_dao or OSMnxStreetGraphDAO(db=self.db)
        graph = dao.load_graph()

        scores_map = self._cargar_scores_por_arista()

        aristas_con_score = 0
        for u, v, _key, data in graph.edges(keys=True, data=True):
            length = data.get("length", 1.0) or 1.0
            composite = scores_map.get((u, v), SCORE_NEUTRO)

            data["cost"] = length * (1 + ALPHA_RISK * composite)
            data["composite_score"] = composite

            if (u, v) in scores_map:
                aristas_con_score += 1

        print(f"  {aristas_con_score}/{graph.number_of_edges()} aristas con score asignado")
        return graph

    def _cargar_scores_por_arista(self) -> dict:
        """
        Carga scores desde RiskScoreRepository y los mapea por (source_node, target_node).
        """
        sql = text("""
            SELECT
                seg.source_node_id,
                seg.target_node_id,
                rs.composite_score
            FROM risk_scores rs
            JOIN street_segments seg ON rs.segment_id = seg.id
            WHERE rs.composite_score IS NOT NULL
        """)

        rows = self.db.execute(sql).fetchall()

        scores_dict = {}
        for source_node, target_node, score in rows:
            scores_dict[(source_node, target_node)] = score

        return scores_dict

    def _nodo_mas_cercano(self, graph: nx.MultiDiGraph, lat: float, lon: float) -> int:
        """
        Encuentra el nodo del grafo más cercano a las coordenadas dadas.
        """
        from math import radians, sin, cos, sqrt, atan2

        mejor_nodo = None
        menor_dist = float("inf")

        # Radio de la Tierra en metros
        R = 6371000

        lat_rad = radians(lat)
        lon_rad = radians(lon)

        for node_id, data in graph.nodes(data=True):
            # data["x"] = longitud, data["y"] = latitud (en grados)
            node_lat = data["y"]
            node_lon = data["x"]

            # Convertir a radianes
            node_lat_rad = radians(node_lat)
            node_lon_rad = radians(node_lon)

            # Fórmula Haversine para distancia en metros
            dlat = node_lat_rad - lat_rad
            dlon = node_lon_rad - lon_rad
            a = sin(dlat / 2) ** 2 + cos(lat_rad) * cos(node_lat_rad) * sin(dlon / 2) ** 2
            c = 2 * atan2(sqrt(a), sqrt(1 - a))
            dist = R * c

            if dist < menor_dist:
                menor_dist = dist
                mejor_nodo = node_id

        return mejor_nodo

    def _extraer_segmentos(self, graph: nx.MultiDiGraph, path_nodes: list) -> list:
        """
        Extrae segmentos del path calculado por Dijkstra.
        """
        segmentos = []

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

            segmentos.append({
                "source_node":     u,
                "target_node":     v,
                "edge_key":        selected_key,
                "name":            edge_data.get("name", "Sin nombre"),
                "length_m":        edge_data.get("length", 0.0) or 0.0,
                "composite_score": edge_data.get("composite_score", SCORE_NEUTRO),
                "coordinates":     coords,
            })

        return segmentos

    def _calcular_security_score(self, segmentos: list) -> int:
        if not segmentos:
            return 50

        longitud_total  = sum(s["length_m"] for s in segmentos)
        suma_ponderada  = sum(s["length_m"] * s["composite_score"] for s in segmentos)

        if longitud_total == 0:
            return 50

        risk_route = suma_ponderada / longitud_total
        return round(100 * (1 - risk_route))

    def _get_categoria(self, security_score: int, segmentos: list = None) -> str:
        """
        Determina categoría de la ruta con degradación (SAF-44).

        Regla de degradación: Si más del 10% de la longitud total es rojo
        (composite_score > 0.60), la ruta se degrada de "Segura" a "Moderada".
        """
        if security_score >= CATEGORIA_SEGURA:
            categoria_base = "Segura"
        elif security_score >= CATEGORIA_MODERADA:
            categoria_base = "Moderada"
        else:
            categoria_base = "Riesgosa"

        if categoria_base == "Segura" and segmentos:
            longitud_total = sum(s["length_m"] for s in segmentos)
            if longitud_total > 0:
                longitud_rojo = sum(
                    s["length_m"] for s in segmentos
                    if s.get("composite_score", SCORE_NEUTRO) > RIESGO_MEDIO
                )
                pct_rojo = longitud_rojo / longitud_total

                # Si > 10% es rojo, degradar a Moderada
                if pct_rojo > DEGRADACION_ROJO_MAX:
                    return "Moderada"

        return categoria_base
