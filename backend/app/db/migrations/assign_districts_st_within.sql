-- Migración: Crear tabla de distritos y asignar segmentos a distritos vía ST_Within

-- Crear tabla de distritos si no existe
CREATE TABLE IF NOT EXISTS districts (
    ubigeo VARCHAR(10) PRIMARY KEY,
    district_name VARCHAR(100) NOT NULL,
    geometry GEOMETRY(POLYGON, 4326) NOT NULL
);

-- Crear índice espacial GIST para optimizar ST_Within queries
CREATE INDEX IF NOT EXISTS idx_districts_geometry ON districts USING GIST (geometry);

-- Poblar distritos desde OSM (admin-level 8 para Lima/Callao)
-- Las geometrías se extraerán desde OSM relations con admin_level=8

-- Una vez la tabla esté poblada, asignar segmentos a distritos con ST_Within
UPDATE street_segments ss
SET district_ubigeo = d.ubigeo
FROM districts d
WHERE ss.district_ubigeo IS NULL
  AND ST_Within(ss.geometry, d.geometry);

-- Verificar que todos los segmentos que intersectan fueron asignados
UPDATE street_segments ss
SET district_ubigeo = d.ubigeo
FROM districts d
WHERE ss.district_ubigeo IS NULL
  AND ST_Intersects(ss.geometry, d.geometry)
  AND ST_Distance(ss.geometry, d.geometry) < 1;  -- Menos de 1 metro de distancia

-- Log de resultados
SELECT 
    COUNT(*) as total_segments,
    COUNT(CASE WHEN district_ubigeo IS NOT NULL THEN 1 END) as assigned_segments,
    COUNT(CASE WHEN district_ubigeo IS NULL THEN 1 END) as unassigned_segments
FROM street_segments;

-- Ver estadísticas por distrito
SELECT 
    district_ubigeo,
    COUNT(*) as segment_count
FROM street_segments
WHERE district_ubigeo IS NOT NULL
GROUP BY district_ubigeo
ORDER BY segment_count DESC;
