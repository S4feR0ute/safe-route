CREATE EXTENSION IF NOT EXISTS postgis;

-- Tabla para el Grafo de Calles
CREATE TABLE IF NOT EXISTS street_segments (
    id SERIAL PRIMARY KEY,
    osm_way_id BIGINT,
    geometry GEOMETRY(LineString, 4326),
    name TEXT,
    length_m FLOAT,
    source_node_id BIGINT,
    target_node_id BIGINT,
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

-- Tabla de Contexto Urbano
CREATE TABLE IF NOT EXISTS urban_context (
    id SERIAL PRIMARY KEY,
    segment_id INTEGER REFERENCES street_segments(id),
    nearby_police_stations INTEGER DEFAULT 0,
    nearby_cameras INTEGER DEFAULT 0,
    lighting_level TEXT,
    road_type TEXT,
    poi_density FLOAT
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
