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
    highway_type TEXT,
    oneway BOOLEAN DEFAULT FALSE,
    source_node_id BIGINT REFERENCES street_nodes(node_id) ON DELETE CASCADE,
    target_node_id BIGINT REFERENCES street_nodes(node_id) ON DELETE CASCADE,
    district_ubigeo VARCHAR(10)
);

-- Tabla de tipos de Crimen y sus Pesos
CREATE TABLE IF NOT EXISTS crime_types_weights (
    id SERIAL PRIMARY KEY,
    subtype_name TEXT UNIQUE,
    danger_weight FLOAT DEFAULT 1.0,
    is_street_crime BOOLEAN DEFAULT TRUE
);

-- Tabla de Criminalidad (datos sin procesar)
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

-- Tabla de Contexto Urbano (policia, camaras, iluminacion, etc)
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

-- Tabla de Scores Compuestos (riesgo por segmento)
CREATE TABLE IF NOT EXISTS risk_scores (
    id SERIAL PRIMARY KEY,
    segment_id INTEGER REFERENCES street_segments(id) ON DELETE CASCADE,
    district_score FLOAT,
    context_score FLOAT,
    report_score FLOAT DEFAULT 0.0,
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

-- Tabla: Usuarios (ciudadanos, moderadores, admins)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    phone_number VARCHAR(20),
    user_type VARCHAR(20) NOT NULL DEFAULT 'citizen',
    moderator_since TIMESTAMP,
    is_verified_moderator BOOLEAN NOT NULL DEFAULT FALSE,
    moderator_role VARCHAR(20),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,

    CONSTRAINT chk_user_type CHECK (user_type IN ('citizen', 'moderator', 'admin')),
    CONSTRAINT chk_moderator_role CHECK (moderator_role IS NULL OR moderator_role IN ('moderator', 'admin'))
);

-- Tabla: Reportes de Incidencias (anónimos, autenticados, con documentos)
CREATE TABLE IF NOT EXISTS incident_reports (
    id VARCHAR(36) PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    incident_type VARCHAR(100) NOT NULL,
    location GEOMETRY(POINT, 4326) NOT NULL,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    description VARCHAR(1000),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    mode INTEGER NOT NULL DEFAULT 1,
    severity_level VARCHAR(20) DEFAULT 'medium',
    has_documents BOOLEAN NOT NULL DEFAULT FALSE,
    document_count INTEGER NOT NULL DEFAULT 0,
    evidence_quality_score FLOAT NOT NULL DEFAULT 0.0,
    validated_at TIMESTAMP,
    validation_notes VARCHAR(1000),
    validated_by_user_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_status CHECK (status IN ('pending', 'validated', 'rejected')),
    CONSTRAINT chk_mode CHECK (mode IN (1, 2, 3)),
    CONSTRAINT chk_severity_level CHECK (severity_level IN ('low', 'medium', 'high', 'critical')),
    CONSTRAINT chk_evidence_quality CHECK (evidence_quality_score >= 0 AND evidence_quality_score <= 100)
);

-- Tabla: Documentos Adjuntos de Reportes (fotos, videos, PDFs, etc)
CREATE TABLE IF NOT EXISTS report_documents (
    id VARCHAR(36) PRIMARY KEY,
    report_id VARCHAR(36) NOT NULL REFERENCES incident_reports(id) ON DELETE CASCADE,
    file_path VARCHAR(500) NOT NULL,
    file_hash_sha256 VARCHAR(64) UNIQUE NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size_bytes INTEGER NOT NULL,
    storage_type VARCHAR(50) DEFAULT 'local',
    uploaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    original_filename VARCHAR(255),
    description VARCHAR(500),

    CONSTRAINT chk_file_type CHECK (file_type IN ('application/pdf', 'image/jpeg', 'image/png', 'image/jpg')),
    CONSTRAINT chk_storage_type CHECK (storage_type IN ('local', 's3', 'gcs'))
);

-- Índices: Ruteo
CREATE INDEX IF NOT EXISTS idx_districts_geometry
    ON districts USING GIST (geometry);

CREATE INDEX IF NOT EXISTS idx_segments_district_ubigeo
    ON street_segments (district_ubigeo)
    WHERE district_ubigeo IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_street_segments_geometry
    ON street_segments USING GIST (geometry);

-- Índices: Usuarios
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_user_type ON users(user_type);
CREATE INDEX IF NOT EXISTS idx_users_is_verified_moderator ON users(is_verified_moderator);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);
CREATE INDEX IF NOT EXISTS idx_users_locked_until ON users(locked_until);
CREATE INDEX IF NOT EXISTS idx_users_deleted_at ON users(deleted_at);

-- Índices: Reportes
CREATE INDEX IF NOT EXISTS idx_incident_reports_user_id ON incident_reports(user_id);
CREATE INDEX IF NOT EXISTS idx_incident_reports_incident_type ON incident_reports(incident_type);
CREATE INDEX IF NOT EXISTS idx_incident_reports_status ON incident_reports(status);
CREATE INDEX IF NOT EXISTS idx_incident_reports_mode ON incident_reports(mode);
CREATE INDEX IF NOT EXISTS idx_incident_reports_has_documents ON incident_reports(has_documents);
CREATE INDEX IF NOT EXISTS idx_incident_reports_severity ON incident_reports(severity_level);
CREATE INDEX IF NOT EXISTS idx_incident_reports_created_at ON incident_reports(created_at);

-- Índices compuestos: Reportes (queries de moderador)
CREATE INDEX IF NOT EXISTS idx_incident_reports_status_created 
    ON incident_reports(status, created_at);

CREATE INDEX IF NOT EXISTS idx_incident_reports_type_created 
    ON incident_reports(incident_type, created_at);

-- Índice espacial: Reportes (queries geográficas)
CREATE INDEX IF NOT EXISTS idx_incident_reports_location 
    ON incident_reports USING GIST (location);

-- Índices: Documentos
CREATE INDEX IF NOT EXISTS idx_report_documents_report_id 
    ON report_documents(report_id);

CREATE INDEX IF NOT EXISTS idx_report_documents_file_hash_sha256 
    ON report_documents(file_hash_sha256);

CREATE INDEX IF NOT EXISTS idx_report_documents_uploaded_at 
    ON report_documents(uploaded_at);

-- Índice compuesto: Documentos
CREATE INDEX IF NOT EXISTS idx_report_documents_report_uploaded 
    ON report_documents(report_id, uploaded_at DESC);