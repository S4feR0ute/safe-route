import networkx as nx
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.interfaces.street_graph_interface import IStreetGraphDAO
from app.repositories.osmnx_street_graph_dao import OSMnxStreetGraphDAO
from app.core.constants import (
    ALPHA_RISK,
    SCORE_NEUTRO,
    CATEGORIA_SEGURA,
    CATEGORIA_MODERADA,
)


class RoutingService:
    """
    Servicio de ruteo usando algoritmo de Dijkstra ponderado.
    """

    def __init__(self, db: Session, graph_dao: IStreetGraphDAO = None):
        self.db = db
        # DIP: dependemos de la abstracción IStreetGraphDAO. Por defecto se usa
        # la implementación OSMnx; es inyectable para tests con grafos sintéticos.
        self._graph_dao = graph_dao

    def calcular_rutas(self, origen_lat: float, origen_lon: float, destino_lat: float, destino_lon: float) -> dict:
        print("Cargando grafo desde la BD...")
        graph = self._cargar_grafo_con_scores()

        if graph.number_of_nodes() == 0:
            raise ValueError("El grafo está vacío. Ejecuta primero ingest_street_graph.py")

        print("Buscando nodos más cercanos al origen y destino...")
        nodo_origen  = self._nodo_mas_cercano(graph, origen_lat, origen_lon)
        nodo_destino = self._nodo_mas_cercano(graph, destino_lat, destino_lon)
        print(f"  Nodo origen: {nodo_origen} | Nodo destino: {nodo_destino}")

        # --- Ruta segura: Dijkstra con costo ponderado por riesgo ---
        print("Calculando ruta segura (Dijkstra ponderado por riesgo)...")
        try:
            path_segura = nx.dijkstra_path(graph, nodo_origen, nodo_destino, weight="cost")
        except nx.NetworkXNoPath:
            raise ValueError("No existe ruta entre los puntos seleccionados")
        except nx.NodeNotFound as e:
            raise ValueError(f"Nodo no encontrado en el grafo: {e}")

        # --- Ruta corta: Dijkstra solo por longitud ---
        print("Calculando ruta corta (Dijkstra por longitud)...")
        try:
            path_corta = nx.dijkstra_path(graph, nodo_origen, nodo_destino, weight="length")
        except nx.NetworkXNoPath:
            path_corta = path_segura  # Si no encuentra ruta corta, usa la segura

        # --- Construir segmentos con geometría y scores ---
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
                "categoria": self._get_categoria(score_segura),
            },
            "ruta_corta": {
                "nodos": path_corta,
                "segmentos": segmentos_corta,
                "longitud_total_m": round(sum(s["length_m"] for s in segmentos_corta), 2),
                "security_score": score_corta,
                "categoria": self._get_categoria(score_corta),
            },
        }

    def _cargar_grafo_con_scores(self) -> nx.MultiDiGraph:
        dao = self._graph_dao or OSMnxStreetGraphDAO(db_session=self.db)
        graph = dao.load_graph()

        scores = self._cargar_scores_por_arista()

        aristas_con_score = 0
        for u, v, _key, data in graph.edges(keys=True, data=True):
            length = data.get("length", 1.0) or 1.0
            composite = scores.get((u, v), SCORE_NEUTRO)

            # Fórmula SAF-43
            data["cost"] = length * (1 + ALPHA_RISK * composite)
            data["composite_score"] = composite

            if (u, v) in scores:
                aristas_con_score += 1

        print(f"  {aristas_con_score}/{graph.number_of_edges()} aristas con score asignado")
        return graph

    def _cargar_scores_por_arista(self) -> dict:
        sql = text("""
            SELECT seg.source_node_id, seg.target_node_id, rs.composite_score
            FROM street_segments seg
            JOIN risk_scores rs ON rs.segment_id = seg.id
        """)
        rows = self.db.execute(sql).fetchall()

        scores = {}
        for row in rows:
            scores[(row[0], row[1])] = row[2]

        print(f"  {len(scores)} scores cargados desde risk_scores")
        return scores

    def _nodo_mas_cercano(self, graph: nx.MultiDiGraph, lat: float, lon: float) -> int:
        mejor_nodo = None
        menor_dist = float("inf")

        for node_id, data in graph.nodes(data=True):
            # data["x"] = longitud, data["y"] = latitud
            dist = (data["y"] - lat) ** 2 + (data["x"] - lon) ** 2
            if dist < menor_dist:
                menor_dist = dist
                mejor_nodo = node_id

        return mejor_nodo

    def _extraer_segmentos(self, graph: nx.MultiDiGraph, path_nodes: list) -> list:
        segmentos = []

        for i in range(len(path_nodes) - 1):
            u = path_nodes[i]
            v = path_nodes[i + 1]

            # Entre dos nodos puede haber varias aristas (MultiDiGraph).
            # Nos quedamos con la de menor costo, que es la que Dijkstra eligió.
            edge_data = min(
                graph[u][v].values(),
                key=lambda d: d.get("cost", d.get("length", 1.0)),
            )

            geom = edge_data.get("geometry")
            if geom:
                coords = list(geom.coords)
            else:
                # Fallback: línea recta entre los dos nodos
                coords = [
                    (graph.nodes[u]["x"], graph.nodes[u]["y"]),
                    (graph.nodes[v]["x"], graph.nodes[v]["y"]),
                ]

            segmentos.append({
                "source_node":     u,
                "target_node":     v,
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

    def _get_categoria(self, security_score: int) -> str:
        if security_score >= CATEGORIA_SEGURA:
            return "Segura"
        elif security_score >= CATEGORIA_MODERADA:
            return "Moderada"
        else:
            return "Riesgosa"
