import osmnx as ox
import networkx as nx
from sqlalchemy import text
from sqlalchemy.orm import Session
from geoalchemy2.shape import to_shape
from app.interfaces.street_graph_interface import IStreetGraphDAO
from app.models.street_network import StreetNode, StreetSegment
from app.models.district_geometry import DistrictGeometry
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
        print(f"  -> {graph.number_of_nodes()} nodos, {graph.number_of_edges()} aristas")
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

    def assign_segments_to_districts_st_within(self) -> dict:
        """
        Asigna cada segmento de calle a su distrito usando ST_Within (PostGIS).
        
        Algoritmo:
        1. ST_Within: Segmentos completamente dentro del polígono del distrito
        2. ST_Intersects: Para segmentos en límites, si no fueron asignados
        
        Returns:
            dict: Estadísticas de la asignación
                {
                    "total_segments": int,
                    "assigned_via_st_within": int,
                    "assigned_via_st_intersects": int,
                    "total_assigned": int,
                    "unassigned": int,
                    "by_district": dict  # Segmentos por UBIGEO
                }
        """
        print("\nAsignación de segmentos a distritos vía ST_Within")
        
        # Verificar si hay distritos en BD
        district_count = self.db.query(DistrictGeometry).count()
        if district_count == 0:
            print("   ADVERTENCIA: No hay distritos en la BD.")
            print("   Ejecuta populate_districts_osm.py primero.")
            return {
                "error": "No districts found in database",
                "total_segments": 0,
                "assigned_via_st_within": 0,
                "assigned_via_st_intersects": 0,
                "total_assigned": 0,
                "unassigned": 0,
            }
        
        print(f"  Distritos en BD: {district_count}")
        
        # Asignar segmentos usando ST_Within (está completamente dentro)
        print("  [1/2] Asignando segmentos dentro de polígonos (ST_Within)...")
        
        query_st_within = text("""
            UPDATE street_segments ss
            SET district_ubigeo = d.ubigeo
            FROM districts d
            WHERE ss.district_ubigeo IS NULL
              AND ST_Within(ss.geometry, d.geometry)
        """)
        
        result_within = self.db.execute(query_st_within)
        self.db.commit()
        assigned_within = result_within.rowcount
        print(f"    -> {assigned_within} segmentos asignados via ST_Within")
        
        # Asignar segmentos en límites usando ST_Intersects
        print("  [2/2] Asignando segmentos en límites (ST_Intersects)...")
        
        query_st_intersects = text("""
            UPDATE street_segments ss
            SET district_ubigeo = (
                SELECT d.ubigeo 
                FROM districts d 
                WHERE ST_Intersects(ss.geometry, d.geometry)
                ORDER BY ST_Distance(ss.geometry, d.geometry) ASC
                LIMIT 1
            )
            WHERE ss.district_ubigeo IS NULL
              AND EXISTS (
                SELECT 1 FROM districts d 
                WHERE ST_Intersects(ss.geometry, d.geometry)
              )
        """)
        
        result_intersects = self.db.execute(query_st_intersects)
        self.db.commit()
        assigned_intersects = result_intersects.rowcount
        print(f"    -> {assigned_intersects} segmentos asignados via ST_Intersects")
        
        # Obtener estadísticas finales
        total_segments = self.db.query(StreetSegment).count()
        assigned_total = self.db.query(StreetSegment).filter(
            StreetSegment.district_ubigeo.isnot(None)
        ).count()
        unassigned = total_segments - assigned_total
        
        # Estadísticas por distrito
        by_district_query = text("""
            SELECT 
                district_ubigeo,
                COUNT(*) as count
            FROM street_segments
            WHERE district_ubigeo IS NOT NULL
            GROUP BY district_ubigeo
            ORDER BY count DESC
        """)
        
        by_district = {}
        for ubigeo, count in self.db.execute(by_district_query).fetchall():
            by_district[ubigeo] = count
        
        # Imprimir resumen
        print(f"\n   Resumen:")
        print(f"    Total de segmentos: {total_segments}")
        print(f"    Asignados (ST_Within): {assigned_within}")
        print(f"    Asignados (ST_Intersects): {assigned_intersects}")
        print(f"    Total asignados: {assigned_total}")
        print(f"    Sin asignar: {unassigned}")
        
        if by_district:
            print(f"\n   Segmentos por distrito (top 10):")
            for i, (ubigeo, count) in enumerate(list(by_district.items())[:10], 1):
                district_obj = self.db.query(DistrictGeometry).filter(
                    DistrictGeometry.ubigeo == ubigeo
                ).first()
                district_name = district_obj.district_name if district_obj else "Unknown"
                print(f"    {i:2}. {ubigeo} ({district_name}): {count:6} segmentos")
        
        if unassigned > 0:
            print(f"\n    {unassigned} segmentos sin asignar. Verifica geometrías.")
        else:
            print(f"\n   ÉXITO: Todos los segmentos fueron asignados a distritos")
        
        return {
            "total_segments": total_segments,
            "assigned_via_st_within": assigned_within,
            "assigned_via_st_intersects": assigned_intersects,
            "total_assigned": assigned_total,
            "unassigned": unassigned,
            "by_district": by_district,
        }
