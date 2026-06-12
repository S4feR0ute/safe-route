import osmnx as ox
import networkx as nx
from shapely.geometry import LineString
from sqlalchemy.orm import Session
from geoalchemy2.shape import to_shape
from app.interfaces.street_graph_interface import IStreetGraphDAO
from app.models.street_network import StreetNode, StreetSegment


class OSMnxStreetGraphDAO(IStreetGraphDAO):
    def __init__(self, db_session: Session, network_type: str = 'drive'):
        self.db = db_session
        self.network_type = network_type
        ox.settings.use_cache = True
        ox.settings.log_console = True

    def extract_graph(self, city_name: str) -> nx.MultiDiGraph:
        print(f"Extrayendo grafo de OSM para: {city_name}...")
        return ox.graph_from_place(city_name, network_type=self.network_type)

    def save_graph(self, graph: nx.MultiDiGraph) -> None:
        print("Preparando nodos (intersecciones)...")
        nodes_to_insert = []
        for node_id, data in graph.nodes(data=True):
            lon, lat = data['x'], data['y']
            # Formato WKT explícito para GeoAlchemy2
            geom_wkt = f"SRID=4326;POINT({lon} {lat})"
            
            node = StreetNode(
                node_id=node_id, 
                geometry=geom_wkt, 
                lat=lat, 
                lon=lon
            )
            nodes_to_insert.append(node)
        
        # Inserción de nodos
        self.db.add_all(nodes_to_insert)
        self.db.flush()
        
        print("Preparando segmentos de calle...")
        segments_to_insert = []
        for u, v, k, data in graph.edges(keys=True, data=True):
            osm_id = data.get('osmid')[0] if isinstance(data.get('osmid'), list) else data.get('osmid')
            name = data.get('name', 'Desconocido')
            name = name[0] if isinstance(name, list) else name
            length = data.get('length', 0.0)
            highway = data.get('highway', 'unclassified')
            highway = highway[0] if isinstance(highway, list) else highway
            oneway = bool(data.get('oneway', False))

            if 'geometry' in data:
                line_wkt = data['geometry'].wkt
            else:
                x1, y1 = graph.nodes[u]['x'], graph.nodes[u]['y']
                x2, y2 = graph.nodes[v]['x'], graph.nodes[v]['y']
                line_wkt = LineString([(x1, y1), (x2, y2)]).wkt
                
            geom_wkt = f"SRID=4326;{line_wkt}"

            segment = StreetSegment(
                osm_way_id=osm_id,
                geometry=geom_wkt,
                name=name,
                length_m=length,
                highway_type=highway,
                oneway=oneway,
                source_node_id=u,
                target_node_id=v
            )
            segments_to_insert.append(segment)

        # Inserción de aristas
        self.db.add_all(segments_to_insert)
        self.db.commit()
        print(f"Grafo guardado exitosamente. {len(nodes_to_insert)} nodos y {len(segments_to_insert)} calles insertadas.")

    def load_graph(self) -> nx.MultiDiGraph:
        print("Reconstruyendo el grafo NetworkX desde la base de datos...")
        
        G = nx.MultiDiGraph()
        G.graph['crs'] = "epsg:4326"

        # Cargar nodos
        nodos_db = self.db.query(StreetNode).all()
        for nodo in nodos_db:
            G.add_node(
                nodo.node_id, 
                x=nodo.lon, 
                y=nodo.lat
            )

        # Cargar segmentos
        segmentos_db = self.db.query(StreetSegment).all()
        for seg in segmentos_db:
            geom_shapely = to_shape(seg.geometry) if seg.geometry is not None else None
            G.add_edge(
                seg.source_node_id,
                seg.target_node_id,
                osmid=seg.osm_way_id,
                name=seg.name,
                length=seg.length_m,
                highway=seg.highway_type,
                oneway=seg.oneway,
                geometry=geom_shapely
            )

        print(f"Grafo reconstruido exitosamente con {G.number_of_nodes()} nodos y {G.number_of_edges()} calles.")
        return G
