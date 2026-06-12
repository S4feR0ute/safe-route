from geoalchemy2.elements import WKTElement
from shapely.geometry import LineString


def setup_osmnx():
    """Activa cache y logs de OSMnx (evita repetir descargas largas)."""
    import osmnx as ox

    ox.settings.use_cache = True
    ox.settings.log_console = True


def district_label_from_place(place_name: str) -> str:
    """'Miraflores, Lima, Peru' -> 'Miraflores'."""
    return place_name.split(",")[0].strip()


def normalize_tag_value(value, default="Desconocido"):
    """
    OSM a veces devuelve listas (ej: name=['Av. Larco', 'Av. Larco']).
    Nos quedamos con el primer valor usable.
    """
    if value is None:
        return default

    if isinstance(value, list):
        if not value:
            return default
        return normalize_tag_value(value[0], default)

    if isinstance(value, float) and value != value:  # NaN
        return default

    text = str(value).strip()
    return text if text else default


def parse_oneway(value) -> bool:
    """Convierte el tag oneway de OSM a True/False."""
    if value in (True, 1, "yes", "true", "1", -1, "-1"):
        return True
    return False


def get_osm_way_id(edge_data: dict):
    """Obtiene un ID numérico de la vía, aunque venga como lista."""
    raw = edge_data.get("osmid")
    if raw is None:
        return None
    if isinstance(raw, list):
        return raw[0] if raw else None
    return raw


def make_point_geometry(lon: float, lat: float):
    return WKTElement(f"POINT({lon} {lat})", srid=4326)


def make_linestring_geometry(graph, u, v, edge_data: dict):
    """Crea la geometría de un segmento usando OSMnx o un fallback simple."""
    if "geometry" in edge_data:
        return WKTElement(edge_data["geometry"].wkt, srid=4326)

    x1, y1 = graph.nodes[u]["x"], graph.nodes[u]["y"]
    x2, y2 = graph.nodes[v]["x"], graph.nodes[v]["y"]
    line = LineString([(x1, y1), (x2, y2)])
    return WKTElement(line.wkt, srid=4326)
