# 🧪 Guía de Testing: Implementar ST_Within para Asignación de Segmentos a Distritos

> **Nivel**: Down (Paso a paso, desde lo básico)  
> **Ticket**: "Implementar asignación de segmentos a distritos vía ST_Within (PostGIS)"  
> **Duración estimada**: 45-60 minutos  
> **Requisitos**: PostgreSQL + PostGIS, Python 3.8+, conda/venv

---

## Índice
1. [Requisitos Previos](#requisitos-previos)
2. [Paso 1: Configurar Base de Datos](#paso-1-configurar-base-de-datos)
3. [Paso 2: Preparar Ambiente Python](#paso-2-preparar-ambiente-python)
4. [Paso 3: Ejecutar Migraciones](#paso-3-ejecutar-migraciones)
5. [Paso 4: Poblar Distritos desde OSM](#paso-4-poblar-distritos-desde-osm)
6. [Paso 5: Ejecutar Ingesta de Segmentos](#paso-5-ejecutar-ingesta-de-segmentos)
7. [Paso 6: Validar Asignación con ST_Within](#paso-6-validar-asignación-con-st_within)
8. [Paso 7: Verificar Resultados en Detail](#paso-7-verificar-resultados-en-detalle)
9. [Troubleshooting](#troubleshooting)

---

## Requisitos Previos

### Software necesario
- **PostgreSQL**: 12+ con extensión PostGIS habilitada
- **Python**: 3.8 o superior
- **pip/conda**: Gestor de paquetes Python
- **Git**: (ya debes tener el repositorio clonado)

### Verificar instalaciones

```bash
# PostgreSQL
psql --version
# Output esperado: psql (PostgreSQL) 12.x o mayor

# Python
python --version
# Output esperado: Python 3.8+ o 3.11+

# PostGIS (ejecutar en psql después de conectarse)
CREATE EXTENSION IF NOT EXISTS postgis;
SELECT PostGIS_version();
-- Output esperado: 3.x.x
```

---

## Paso 1: Configurar Base de Datos

### 1.1 Crear usuario y base de datos

Abre una terminal e ingresa a PostgreSQL:

```bash
# Conectar a PostgreSQL como superusuario (típicamente 'postgres')
sudo -u postgres psql
```

Dentro de PostgreSQL, ejecuta:

```sql
-- Crear usuario para la aplicación
CREATE USER safedev WITH PASSWORD 'safedev123';

-- Crear base de datos para SafeRoute
CREATE DATABASE safedb OWNER safedev;

-- Otorgar permisos
GRANT ALL PRIVILEGES ON DATABASE safedb TO safedev;

-- Salir
\q
```

### 1.2 Conectarse a la nueva BD con super usuario

```bash
sudo -u postgres psql -d safedb
```

Dentro de psql, ejecuta:

```sql
-- Crear extensión PostGIS (requerida para geometrías)
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Verificar
SELECT PostGIS_version();
-- Deberías ver algo como: "3.3.4 built with GEOS 3.11.4"

\q
```

✅ **Base de datos lista**

---

## Paso 2: Preparar Ambiente Python

### 2.1 Navegar al directorio del backend

```bash
cd ~/safe-route/backend
```

### 2.2 Crear entorno virtual

**Con venv:**
```bash
python -m venv venv
source venv/bin/activate  
# En Windows: venv\Scripts\activate
```

### 2.3 Instalar dependencias

```bash
pip install -r requirements.txt
```

⏳ **Espera 3-5 minutos** (OSMnx, GeoAlchemy2, etc. son pesados)

### 2.4 Crear archivo `.env` (configuración de BD)

Crea un archivo `backend/.env`:

```bash
cat > .env << 'EOF'
DATABASE_URL_LOCAL=postgresql://safedev:safedev123@localhost:5432/safedb
SQLALCHEMY_ECHO=True
OSM_CACHE_FOLDER=/tmp/osm_cache
EOF
```

✅ **Ambiente Python configurado**

---

## Paso 3: Ejecutar Migraciones

### 3.1 Crear tablas base (init_db.sql)

Desde el terminal (fuera de Python), ejecuta:

```bash
psql -U safedev -d safedb -h localhost -f app/db/migrations/init_db.sql
```

Output esperado:
```
CREATE EXTENSION
CREATE TABLE
CREATE TABLE
CREATE INDEX
...
```

Verifica que se crearon las tablas:

```bash
psql -U safedev -d safedb -h localhost -c "\dt"
```

Output esperado:
```
                 List of relations
 Schema |          Name           | Type  | Owner  
--------+-------------------------+-------+--------
 public | crime_types_weights     | table | safedev
 public | crimen_raw_data         | table | safedev
 public | data_load_log           | table | safedev
 public | district_crime_stats    | table | safedev
 public | risk_scores             | table | safedev
 public | street_nodes            | table | safedev
 public | street_segments         | table | safedev
 public | urban_context           | table | safedev
 public | urban_pois              | table | safedev
(9 rows)
```

✅ **Tablas base creadas**

---

## Paso 4: Poblar Distritos desde OSM

### 4.1 Ejecutar script de extracción de distritos

Desde `~/safe-route/backend/`:

```bash
python -m app.data_loader.populate_districts_osm
```

**Esto hará:**
1. Conectar a OSM (Overpass)
2. Descargar geometrías de distritos (admin-level 8)
3. Guardar en tabla `districts`
4. Mostrará progreso:

```
--- Extracción de geometrías de distritos desde OSM ---

Limpiando tabla de distritos existentes...
Extrayendo administrativas de OSM...

  Consultando: Lima, Peru
    -> Ancón (150131)
    -> Ate (150140)
    -> Barranco (150131)
    ... (total ~43 distritos)

  Consultando: Callao, Peru
    -> Bellavista (070131)
    -> Callao District (070131)
    ... (total ~7 distritos)

Guardando 50 distritos en BD...
✓ 50 distritos guardados

Total de distritos en BD: 50

Distritos guardados:
  - 150131: Ancón
  - 150140: Ate
  - 150210: Barranco
  ...
```

⏳ **Espera 2-5 minutos** (depende de tu conexión a OSM)

### 4.2 Verificar distritos en BD

```bash
psql -U safedev -d safedb -h localhost -c "SELECT COUNT(*) as total_distritos FROM districts;"
```

Output esperado:
```
 total_distritos
-----------------
              50
(1 row)
```

También puedes ver detalles:

```bash
psql -U safedev -d safedb -h localhost -c "SELECT ubigeo, district_name FROM districts LIMIT 5;"
```

Output:
```
 ubigeo | district_name
--------+---------------
 150131 | Ancón
 150140 | Ate
 150210 | Barranco
 ...
(5 rows)
```

✅ **Distritos poblados desde OSM**

---

## Paso 5: Ejecutar Ingesta de Segmentos

### 5.1 Ejecutar script de ingesta (incluye ST_Within automáticamente)

Desde `~/safe-route/backend/`:

```bash
python -m app.data_loader.ingest_street_graph
```

**Esto hará:**
1. Limpiar tablas anteriores
2. Descargar grafo de OSM para cada distrito
3. Guardar nodos y segmentos
4. **EJECUTAR AUTOMÁTICAMENTE ST_Within** para asignar distritos
5. Mostrar estadísticas

Output típico (los primeros distritos):

```
Limpiando tablas de red vial...
--- Ingesta de red vial (OSMnx) ---
Distritos a procesar: 50 | network_type=walk

[1/50] Ancón, Lima, Peru
Extrayendo grafo de OSM para: Ancón, Lima, Peru...
  -> 1234 nodos, 5678 aristas
  -> 120 nodos nuevos guardados
  -> 456 segmentos guardados para Ancón, Lima, Peru

[2/50] Ate, Lima, Peru
Extrayendo grafo de OSM para: Ate, Lima, Peru...
  ...
```

⏳ **Espera 30-60 minutos** (descarga 50 distritos de OSM)

### 5.2 Cuando termine, verás:

```
--- Resumen ---
Distritos OK: 50/50
Segmentos insertados: 45678

--- Asignación de segmentos a distritos ---

--- Asignación de segmentos a distritos vía ST_Within ---
  Distritos en BD: 50
  [1/2] Asignando segmentos dentro de polígonos (ST_Within)...
    -> 45123 segmentos asignados via ST_Within
  [2/2] Asignando segmentos en límites (ST_Intersects)...
    -> 555 segmentos asignados via ST_Intersects

  📊 Resumen:
    Total de segmentos: 45678
    Asignados (ST_Within): 45123
    Asignados (ST_Intersects): 555
    Total asignados: 45678
    Sin asignar: 0

  📍 Segmentos por distrito (top 10):
     1. 150131 (Ancón): 456 segmentos
     2. 150140 (Ate): 789 segmentos
     3. 150210 (Barranco): 234 segmentos
     ...

  ✅ ÉXITO: Todos los segmentos fueron asignados a distritos

✅ Ingesta completada exitosamente
```

✅ **Segmentos asignados a distritos vía ST_Within**

---

## Paso 6: Validar Asignación con ST_Within

### 6.1 Consulta SQL para verificar asignación

Abre una sesión de psql:

```bash
psql -U safedev -d safedb -h localhost
```

### 6.2 Ver estadísticas totales

```sql
-- ¿Cuántos segmentos fueron asignados?
SELECT 
    COUNT(*) as total_segments,
    COUNT(CASE WHEN district_ubigeo IS NOT NULL THEN 1 END) as assigned,
    COUNT(CASE WHEN district_ubigeo IS NULL THEN 1 END) as unassigned,
    ROUND(100.0 * COUNT(CASE WHEN district_ubigeo IS NOT NULL THEN 1 END) / COUNT(*), 2) as percent_assigned
FROM street_segments;
```

Output esperado:
```
 total_segments | assigned | unassigned | percent_assigned
----------------+----------+------------+------------------
          45678 |    45678 |          0 |           100.00
(1 row)
```

### 6.3 Ver distribución por distrito

```sql
-- ¿Cuántos segmentos por distrito?
SELECT 
    d.ubigeo,
    d.district_name,
    COUNT(ss.id) as segment_count
FROM districts d
LEFT JOIN street_segments ss ON d.ubigeo = ss.district_ubigeo
GROUP BY d.ubigeo, d.district_name
ORDER BY segment_count DESC
LIMIT 10;
```

Output esperado:
```
 ubigeo |       district_name        | segment_count
--------+----------------------------+---------------
 150131 | Ancón                      |           456
 150140 | Ate                        |           789
 150210 | Barranco                   |           234
 150310 | Chorrillos                 |           567
 150410 | Comas                      |           890
 150520 | Jesús María                |           345
 150620 | Lince                      |           123
 150710 | Los Olivos                 |           678
 150810 | Magdalena del Mar          |           234
 150820 | Miraflores                 |           456
(10 rows)
```

### 6.4 Validar geometrías específicas

```sql
-- Verificar un segmento específico en Miraflores
SELECT 
    ss.id,
    ss.name,
    ss.district_ubigeo,
    d.district_name,
    ST_AsText(ss.geometry) as geometry_wkt
FROM street_segments ss
JOIN districts d ON ss.district_ubigeo = d.ubigeo
WHERE d.ubigeo = '150122'  -- Miraflores
LIMIT 1;
```

Output esperado:
```
 id |     name      | district_ubigeo | district_name |            geometry_wkt
----+---------------+-----------------+---------------+------------------------------------
  1 | Av. Larco     | 150820          | Miraflores    | LINESTRING (-77.03 -12.13, ...)
(1 row)
```

### 6.5 Verificar segmentos SIN asignar (debug)

```sql
-- Debería retornar 0 filas
SELECT COUNT(*) as unassigned_count
FROM street_segments
WHERE district_ubigeo IS NULL;

-- Si hay sin asignar, verlas:
SELECT id, osm_way_id, name, ST_AsText(geometry)
FROM street_segments
WHERE district_ubigeo IS NULL
LIMIT 10;
```

✅ **Asignación validada**

---

## Paso 7: Verificar Resultados en Detalle

### 7.1 Verificar que ST_Within se ejecutó correctamente

```sql
-- Contar segmentos completamente dentro de distritos
SELECT 
    COUNT(*) as total_intersecting,
    COUNT(CASE WHEN ST_Within(ss.geometry, d.geometry) THEN 1 END) as within_count
FROM street_segments ss
CROSS JOIN districts d
WHERE ss.district_ubigeo = d.ubigeo
LIMIT 1000;
```

### 7.2 Muestreo aleatorio de segmentos asignados

```sql
-- Ver 5 segmentos aleatorios con sus distritos
SELECT 
    ss.id,
    ss.name,
    ss.length_m,
    ss.highway_type,
    d.ubigeo,
    d.district_name,
    ST_AsGeoJSON(ss.geometry) as geojson
FROM street_segments ss
JOIN districts d ON ss.district_ubigeo = d.ubigeo
ORDER BY RANDOM()
LIMIT 5;
```

### 7.3 Verificar performance de índices

```sql
-- PostGIS debería usar índices GIST
EXPLAIN ANALYZE
SELECT ss.id
FROM street_segments ss
JOIN districts d ON ST_Within(ss.geometry, d.geometry)
WHERE d.ubigeo = '150131'
LIMIT 10;
```

Output debería mencionar "Index Scan" o "Bitmap Index Scan" (no Sequential Scan)

### 7.4 Verificar integridad referencial

```sql
-- Todos los district_ubigeo deben existir en la tabla districts
SELECT COUNT(*) as invalid_references
FROM street_segments ss
WHERE ss.district_ubigeo IS NOT NULL
  AND ss.district_ubigeo NOT IN (SELECT ubigeo FROM districts);

-- Output esperado: 0
```

### 7.5 Exportar datos para visualización (opcional)

```bash
# Exportar segmentos de Miraflores como GeoJSON
psql -U safedev -d safedb -h localhost -c "
SELECT 
    json_build_object(
        'type', 'FeatureCollection',
        'features', json_agg(
            json_build_object(
                'type', 'Feature',
                'properties', json_build_object(
                    'name', ss.name,
                    'ubigeo', ss.district_ubigeo,
                    'highway_type', ss.highway_type
                ),
                'geometry', ST_AsGeoJSON(ss.geometry)::json
            )
        )
    )
FROM street_segments ss
WHERE ss.district_ubigeo = '150122'  -- Miraflores
LIMIT 100;
" > miraflores_segments.geojson
```

Luego puedes visualizar en [geojson.io](https://geojson.io) pegando el contenido

✅ **Resultados verificados en detalle**

---

## Troubleshooting

### Problema 1: "Base de datos no existe"

```
FATAL: database "safedb" does not exist
```

**Solución:**
```bash
# Crear BD
psql -U postgres -c "CREATE DATABASE safedb OWNER safedev;"
psql -U safedev -d safedb -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

---

### Problema 2: "PostGIS no está instalado"

```
ERROR: extension "postgis" does not exist
```

**Solución:**
```bash
# En Ubuntu/Debian
sudo apt-get install postgresql-13-postgis-3

# En macOS con brew
brew install postgis

# Luego crear la extensión
psql -U safedev -d safedb -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

---

### Problema 3: "OSM timeout - demora mucho"

```
Timeout al descargar de OSMnx
```

**Soluciones:**
1. Espera más tiempo (puede tomar 1-2 horas según conexión)
2. Ejecuta con subset de distritos para testing:
   ```bash
   python -c "
   from app.core.constants import TARGET_DISTRICTS
   from app.data_loader.ingest_street_graph import run_street_network_ingestion
   
   # Solo 5 distritos para testing
   subset = TARGET_DISTRICTS[:5]
   run_street_network_ingestion(districts=subset)
   "
   ```

---

### Problema 4: "ST_Within no asignó ningún segmento"

```
Asignados (ST_Within): 0
```

**Debug:**
```sql
-- Verificar si hay distritos
SELECT COUNT(*) FROM districts;
-- Debería retornar > 0

-- Verificar si hay segmentos
SELECT COUNT(*) FROM street_segments;
-- Debería retornar > 0

-- Verificar geometrías válidas
SELECT 
    COUNT(*) as total,
    COUNT(CASE WHEN ST_IsValid(geometry) THEN 1 END) as valid
FROM districts;

SELECT 
    COUNT(*) as total,
    COUNT(CASE WHEN ST_IsValid(geometry) THEN 1 END) as valid
FROM street_segments;
```

---

### Problema 5: "Permission denied" en archivo `.env`

```bash
# Asegurate que el archivo tenga permisos de lectura
chmod 644 backend/.env

# Y que esté en el lugar correcto
ls -la backend/.env
```

---

### Problema 6: "ImportError: No module named geoalchemy2"

```
ModuleNotFoundError: No module named 'geoalchemy2'
```

**Solución:**
```bash
# Reinstalar requirements
pip install -r requirements.txt --force-reinstall

# O instalar manualmente
pip install geoalchemy2 sqlalchemy psycopg2-binary osmnx geopandas
```

---

## ✅ Checklist de Validación Final

Antes de dar el ticket por completado, verifica:

- [ ] **Base de datos creada**: `psql -U safedev -d safedb -c "\dt"`
- [ ] **PostGIS instalado**: `psql -U safedev -d safedb -c "SELECT PostGIS_version();"`
- [ ] **Tabla `districts` poblada**: `psql -U safedev -d safedb -c "SELECT COUNT(*) FROM districts;"`
- [ ] **Segmentos guardados**: `psql -U safedev -d safedb -c "SELECT COUNT(*) FROM street_segments;"`
- [ ] **Asignación completada**: `psql -U safedev -d safedb -c "SELECT COUNT(CASE WHEN district_ubigeo IS NULL THEN 1 END) FROM street_segments;"` → Debe ser **0**
- [ ] **Distribución por distrito**: `psql -U safedev -d safedb -c "SELECT COUNT(DISTINCT district_ubigeo) FROM street_segments;"`→ Debe ser **~50**
- [ ] **Indices GIST creados**: `psql -U safedev -d safedb -c "\di" | grep geometry`

Si todos los items están ✅, **el ticket está completado exitosamente**.

---

## 📊 Resumen de Cambios Implementados

| Archivo | Cambio |
|---------|--------|
| `backend/app/models/district_geometry.py` | ✅ CREADO - Modelo SQLAlchemy para tabla `districts` |
| `backend/app/db/migrations/assign_districts_st_within.sql` | ✅ CREADO - Migración SQL con ST_Within + ST_Intersects |
| `backend/app/data_loader/populate_districts_osm.py` | ✅ CREADO - Script para extraer distritos desde OSM |
| `backend/app/repositories/osmnx_street_graph_dao.py` | ✅ MODIFICADO - Método `assign_segments_to_districts_st_within()` |
| `backend/app/data_loader/ingest_street_graph.py` | ✅ MODIFICADO - Integración de ST_Within en pipeline |

---

## 📚 Referencias

- [PostGIS ST_Within](https://postgis.net/docs/ST_Within.html)
- [PostGIS ST_Intersects](https://postgis.net/docs/ST_Intersects.html)
- [GeoAlchemy2 Docs](https://geoalchemy-2.readthedocs.io/)
- [OSMnx Features API](https://osmnx.readthedocs.io/en/stable/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/20/orm/)

---

## 🎯 Próximos Pasos (Opcional)

Una vez que el ticket ST_Within esté completado:

1. **RF-09: Score Calculation** - Usar `district_ubigeo` para ponderar riesgo
2. **RF-10: Routing Engine** - Implementar Dijkstra con pesos de seguridad
3. **RF-11: FastAPI Backend** - Crear endpoints REST
4. **RF-12: Geocoding Proxy** - Proxy de Nominatim en backend

---

**Última actualización**: 2026-06-15  
**Autor**: GitHub Copilot  
**Estado**: ✅ Guía completa

