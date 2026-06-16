CREATE EXTENSION IF NOT EXISTS postgis;

-- Tabla para los Nodos del Grafo (Intersecciones/Cruces)
CREATE TABLE IF NOT EXISTS street_nodes (
    node_id BIGINT PRIMARY KEY,
    geometry GEOMETRY(Point, 4326),
    lat FLOAT,
    lon FLOAT
);

-- Tabla para las Aristas (Segmentos de Calle)
CREATE TABLE IF NOT EXISTS street_segments (
    id SERIAL PRIMARY KEY,
    osm_way_id BIGINT,
    geometry GEOMETRY(LineString, 4326),
    name TEXT,
    length_m FLOAT,
    highway_type TEXT,             -- Residencial, primaria, autopista, etc.
    oneway BOOLEAN DEFAULT FALSE,  -- Sentido de la calle (crucial para ruteo)
    source_node_id BIGINT REFERENCES street_nodes(node_id) ON DELETE CASCADE,
    target_node_id BIGINT REFERENCES street_nodes(node_id) ON DELETE CASCADE,
    district_ubigeo VARCHAR(10)
);

-- Tabla de tipos de Crimen y sus Pesos
CREATE TABLE IF NOT EXISTS crime_types_weights (
    id SERIAL PRIMARY KEY,
    subtype_name TEXT UNIQUE,
    danger_weight FLOAT DEFAULT 1.0,
    is_street_crime BOOLEAN DEFAULT TRUE -- Para filtrar lo que no es de calle
);

-- Tabla de Criminalidad
CREATE TABLE IF NOT EXISTS crimen_raw_data (
    id SERIAL PRIMARY KEY,
    district_ubigeo VARCHAR(10),
    district_name TEXT,
    period VARCHAR(7),
    crime_type TEXT,
    incident_count INTEGER DEFAULT 0
);

-- Tabla de tasas de criminalidad por distrito
CREATE TABLE IF NOT EXISTS district_crime_stats (
    id SERIAL PRIMARY KEY,
    district_ubigeo VARCHAR(10) UNIQUE,
    district_name TEXT,
    total_incidents_count INTEGER,
    violent_incidents_count INTEGER,
    weighted_crime_rate FLOAT
);

-- Tabla para la Infraestructura Urbana (POIs)
CREATE TABLE IF NOT EXISTS urban_pois (
    id SERIAL PRIMARY KEY,
    osm_id VARCHAR UNIQUE,
    poi_type VARCHAR,
    name VARCHAR,
    geometry GEOMETRY(Point, 4326)
);

-- Tabla de Contexto Urbano
CREATE TABLE IF NOT EXISTS urban_context (
    id SERIAL PRIMARY KEY,
    segment_id INTEGER REFERENCES street_segments(id) ON DELETE CASCADE,
    nearby_police_stations INTEGER DEFAULT 0,
    nearby_cameras INTEGER DEFAULT 0,
    lighting_level TEXT,
    road_type TEXT,
    poi_density FLOAT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de Scores Compuestos
CREATE TABLE IF NOT EXISTS risk_scores (
    id SERIAL PRIMARY KEY,
    segment_id INTEGER REFERENCES street_segments(id),
    district_score FLOAT,
    context_score FLOAT,
    composite_score FLOAT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Log de Auditoría para el Data Loader
CREATE TABLE IF NOT EXISTS data_load_log (
    id SERIAL PRIMARY KEY,
    source TEXT,
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    records_processed INTEGER,
    status TEXT
);

-- Tabla de polígonos de distritos
CREATE TABLE IF NOT EXISTS districts (
    id SERIAL PRIMARY KEY,
    ubigeo VARCHAR(10) UNIQUE,
    name TEXT,
    geometry GEOMETRY(Polygon, 4326)
);

-- Índice espacial para acelerar las consultas ST_Within
CREATE INDEX IF NOT EXISTS idx_districts_geometry 
    ON districts USING GIST (geometry);

CREATE INDEX IF NOT EXISTS idx_segments_district_ubigeo
    ON street_segments (district_ubigeo)
    WHERE district_ubigeo IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_street_segments_geometry
    ON street_segments USING GIST (geometry);