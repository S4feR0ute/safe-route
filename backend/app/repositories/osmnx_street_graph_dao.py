import osmnx as ox
import networkx as nx
from sqlalchemy.orm import Session
from geoalchemy2.shape import to_shape
from app.core.constants import GEOCODE_QUERY_OVERRIDES
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

    def __init__(self, db: Session, network_type: str = "walk"):
        self.db = db
        self.network_type = network_type
        self._node_ids_in_db = None
        setup_osmnx()

    def _known_node_ids(self) -> set:
        if self._node_ids_in_db is None:
            rows = self.db.query(StreetNode.node_id).all()
            self._node_ids_in_db = {row[0] for row in rows}
        return self._node_ids_in_db

    CHUNK_SIZE = 50_000

    def extract_graph(self, place_name) -> nx.MultiDiGraph:
        """
        Descarga el grafo peatonal desde OSM (place_name puede ser un lugar "Miraflores, Lima, Peru")."""
        label = place_name if isinstance(place_name, str) else f"{len(place_name)} lugares (unión)"
        print(f"Extrayendo grafo de OSM para: {label}...")

        # Algunos nombres son ambiguos en texto libre para Nominatim; en esos casos se usa una query estructurada.
        if isinstance(place_name, list):
            query = [GEOCODE_QUERY_OVERRIDES.get(p, p) for p in place_name]
        else:
            query = GEOCODE_QUERY_OVERRIDES.get(place_name, place_name)

        graph = ox.graph_from_place(query, network_type=self.network_type)
        print(f"  -> {graph.number_of_nodes()} nodos, {graph.number_of_edges()} aristas")
        return graph

    def save_graph(self, graph: nx.MultiDiGraph, place_name: str) -> int:
        """Persiste nodos y segmentos por lotes (CHUNK_SIZE) con progreso."""
        known_nodes = self._known_node_ids()

        buffer = []
        total_nodes = 0
        for node_id, data in graph.nodes(data=True):
            if node_id in known_nodes:
                continue

            lon, lat = data["x"], data["y"]
            buffer.append(
                StreetNode(
                    node_id=node_id,
                    geometry=make_point_geometry(lon, lat),
                    lat=lat,
                    lon=lon,
                )
            )
            known_nodes.add(node_id)
            if len(buffer) >= self.CHUNK_SIZE:
                total_nodes += self._flush_chunk(buffer, total_nodes, "nodos")

        total_nodes += self._flush_chunk(buffer, total_nodes, "nodos")
        print(f"  -> {total_nodes} nodos guardados")

        total_segments = 0
        for u, v, _key, data in graph.edges(keys=True, data=True):
            if u not in known_nodes or v not in known_nodes:
                continue

            buffer.append(
                StreetSegment(
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
            )
            if len(buffer) >= self.CHUNK_SIZE:
                total_segments += self._flush_chunk(buffer, total_segments, "segmentos")

        total_segments += self._flush_chunk(buffer, total_segments, "segmentos")
        print(f"  -> {total_segments} segmentos guardados para {place_name}")

        self._node_ids_in_db = known_nodes
        return total_segments

    def _flush_chunk(self, buffer: list, done: int, label: str) -> int:
        """Inserta y commitea el lote acumulado; devuelve cuántos insertó."""
        if not buffer:
            return 0
        count = len(buffer)
        self.db.add_all(buffer)
        self.db.commit()
        self.db.expunge_all()  # libera los objetos ORM ya persistidos
        buffer.clear()
        print(f"  ... {done + count} {label}")
        return count

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

        print(f"Grafo reconstruido: {graph.number_of_nodes()} nodos, {graph.number_of_edges()} calles.")
        return graph