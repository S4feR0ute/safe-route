import osmnx as ox
import networkx as nx
from sqlalchemy.orm import Session
from geoalchemy2.shape import to_shape

from app.interfaces.street_graph_interface import IStreetGraphDAO
from app.models.street_network import StreetNode, StreetSegment
from app.utils.osm_helpers import (
    setup_osmnx,
    normalize_tag_value,
    parse_oneway,
    get_osm_way_id,
    make_point_geometry,
    make_linestring_geometry,
)


class OSMnxStreetGraphDAO(IStreetGraphDAO):
    """DAO para extraer y guardar el grafo de calles usando OSMnx."""

    def __init__(self, db_session: Session, network_type: str = "walk"):
        self.db = db_session
        self.network_type = network_type
        self._node_ids_in_db = None
        setup_osmnx()

    def _known_node_ids(self) -> set:
        if self._node_ids_in_db is None:
            rows = self.db.query(StreetNode.node_id).all()
            self._node_ids_in_db = {row[0] for row in rows}
        return self._node_ids_in_db

    def extract_graph(self, place_name: str) -> nx.MultiDiGraph:
        print(f"Extrayendo grafo de OSM para: {place_name}...")
        graph = ox.graph_from_place(place_name, network_type=self.network_type)
        print(
            f"  -> {graph.number_of_nodes()} nodos, "
            f"{graph.number_of_edges()} aristas"
        )
        return graph

    def save_graph(self, graph: nx.MultiDiGraph, place_name: str) -> int:
        known_nodes = self._known_node_ids()
        new_nodes = []

        for node_id, data in graph.nodes(data=True):
            if node_id in known_nodes:
                continue

            lon, lat = data["x"], data["y"]
            new_nodes.append(
                StreetNode(
                    node_id=node_id,
                    geometry=make_point_geometry(lon, lat),
                    lat=lat,
                    lon=lon,
                )
            )
            known_nodes.add(node_id)

        if new_nodes:
            self.db.add_all(new_nodes)
            self.db.flush()
            print(f"  -> {len(new_nodes)} nodos nuevos guardados")

        segments = []
        for u, v, _key, data in graph.edges(keys=True, data=True):
            if u not in known_nodes or v not in known_nodes:
                continue

            segment = StreetSegment(
                osm_way_id=get_osm_way_id(data),
                geometry=make_linestring_geometry(graph, u, v, data),
                name=normalize_tag_value(data.get("name")),
                length_m=float(data.get("length", 0.0) or 0.0),
                highway_type=normalize_tag_value(
                    data.get("highway"), default="unclassified"
                ),
                oneway=parse_oneway(data.get("oneway", False)),
                source_node_id=u,
                target_node_id=v,
            )
            segments.append(segment)

        if segments:
            self.db.add_all(segments)

        if new_nodes or segments:
            self.db.commit()
            print(f"  -> {len(segments)} segmentos guardados para {place_name}")
        else:
            print(f"  -> Sin datos nuevos para {place_name}")

        self._node_ids_in_db = known_nodes
        return len(segments)

    def load_graph(self) -> nx.MultiDiGraph:
        print("Reconstruyendo el grafo NetworkX desde la base de datos...")

        graph = nx.MultiDiGraph()
        graph.graph["crs"] = "epsg:4326"

        for node in self.db.query(StreetNode).all():
            graph.add_node(node.node_id, x=node.lon, y=node.lat)

        for segment in self.db.query(StreetSegment).all():
            geometry = to_shape(segment.geometry) if segment.geometry else None
            graph.add_edge(
                segment.source_node_id,
                segment.target_node_id,
                osmid=segment.osm_way_id,
                name=segment.name,
                length=segment.length_m,
                highway=segment.highway_type,
                oneway=segment.oneway,
                geometry=geometry,
            )

        print(
            f"Grafo reconstruido: {graph.number_of_nodes()} nodos, "
            f"{graph.number_of_edges()} calles."
        )
        return graph
