# SAF-15: Criterios de Aceptación para RF-07 y RF-08

## RF-07: Ingestar datos de criminalidad

### Fuente de datos verificada

- **Archivo**: `Base_datos_SIDPOL_Marzo2026.xlsx` (27 MB)
- **URL de descarga**: https://datosabiertos.gob.pe/dataset/denuncias-policiales-1
- **Hoja a usar**: `Temp5` (datos por distrito con UBIGEO y tipo de delito principal)
- **Hoja complementaria**: `Temp5.2` (datos por distrito con modalidad específica)
- **Nota**: La fuente del Observatorio MININTER fue descartada (ticket SAF-21 archivado) porque proviene de la misma base SIDPOL y generaría datos duplicados.

### Estructura de la hoja Temp5

| Columna | Tipo | Descripción | Ejemplo |
|---------|------|-------------|---------|
| ANIO | string | Año del registro | "2018" |
| MES | string | Mes del registro (1-12) | "1" |
| DPTO_HECHO_NEW | string | Departamento | "LIMA METROPOLITANA" |
| PROV_HECHO | string | Provincia | "LIMA" |
| DIST_HECHO | string | Nombre del distrito | "ATE" |
| UBIGEO_HECHO | string | Código UBIGEO del distrito (6 dígitos) | "150103" |
| PRINCIPALES_TIPOS | string | Categoría del delito | "Delitos patrimoniales" |
| n_dist_ID_DGC | integer | Cantidad de denuncias | 401 |
| DIST_EMERGENCIA | integer | Indicador de distrito en emergencia (0 o 1) | 1 |

### Categorías de delito disponibles

| Categoría | Clasificación para el score |
|-----------|---------------------------|
| Delitos contra la vida, el cuerpo y la salud | **Violento** (peso alto) |
| Delitos contra la libertad | **Violento** (peso alto) |
| Delitos patrimoniales | **Patrimonial** (peso medio) |
| Delitos contra la seguridad pública | **Patrimonial** (peso medio) |
| Delitos contra la administración pública | **Otro** (peso bajo) |
| Otros delitos | **Otro** (peso bajo) |

### Modalidades disponibles (hoja Temp5.2)

| Modalidad | Presente en Lima Metropolitana |
|-----------|-------------------------------|
| Robo | Sí |
| Hurto | Sí |
| Estafa | Sí |
| Extorsión | Sí |
| Otros | Sí |

### Datos verificados de Lima Metropolitana

- **Nombre del filtro**: `DPTO_HECHO_NEW == "LIMA METROPOLITANA"` (no "LIMA")
- **Total de registros para Lima**: 23,256 filas
- **Distritos**: 43 distritos con UBIGEO
- **Rango temporal**: Enero 2018 a Febrero 2026 (97 meses)
- **Registros por distrito por mes**: ~6 filas promedio (una por cada categoría de delito)

### Criterios de aceptación

| ID | Criterio | Verificación |
|----|----------|-------------|
| CA-07-01 | El script descarga o lee el archivo XLSX de SIDPOL sin errores | Ejecutar script; no debe haber excepciones de lectura |
| CA-07-02 | El script filtra correctamente por `DPTO_HECHO_NEW == "LIMA METROPOLITANA"` | El DataFrame filtrado debe tener exactamente 23,256 filas (para el archivo actual) |
| CA-07-03 | El script identifica los 43 distritos de Lima Metropolitana con sus UBIGEO | Verificar que existen los 43 distritos. Lista de UBIGEO empieza en 150101 (Lima/Cercado) y termina en 150143 (Santa Rosa) |
| CA-07-04 | El script calcula la tasa de criminalidad total por distrito para el periodo más reciente | Para cada distrito, sumar `n_dist_ID_DGC` del último año disponible. El resultado debe ser un número positivo |
| CA-07-05 | El script calcula la tasa ponderada diferenciando delitos violentos de patrimoniales | Los delitos "contra la vida" y "contra la libertad" deben tener mayor peso que "patrimoniales". La fórmula debe ser documentada |
| CA-07-06 | Los datos se insertan correctamente en la tabla `district_crime_rates` | Verificar que la tabla tiene 43 filas (una por distrito) con los campos: district_ubigeo, district_name, total_incidents, violent_incidents, property_incidents, weighted_crime_rate |
| CA-07-07 | No se generan registros duplicados al ejecutar el script más de una vez | Ejecutar dos veces; la tabla debe tener las mismas 43 filas (upsert, no insert doble) |
| CA-07-08 | El script registra su ejecución en la tabla `data_load_log` | Debe existir un registro con source="SIDPOL", timestamps de inicio/fin, registros procesados, y status="SUCCESS" o "ERROR" |

### Notas para el desarrollador

- El archivo viene en formato XLSX, no CSV. Usar `pandas.read_excel()` con `sheet_name='Temp5'`.
- Los campos ANIO y MES son strings, no integers. Convertir para operaciones de filtro temporal.
- Para el MVP, usar los datos del último año completo disponible (2025). La posibilidad de elegir periodo se puede agregar después.
- La hoja `Temp5.2` (con modalidades Robo, Hurto, etc.) puede usarse como fuente complementaria para RF-12 (ponderar por tipo de delito).

---

## RF-08: Ingestar grafo y contexto urbano de OSM

### Fuente de datos

- **API**: Overpass API (https://overpass-api.de) para contexto urbano
- **Librería**: OSMnx (Python) para el grafo de calles
- **Cobertura**: Lima Metropolitana (bounding box aproximado: -12.52 a -11.57 lat, -77.19 a -76.62 lon)
- **Network type**: `walk` (red peatonal)

### Datos a extraer del grafo de calles

| Dato | Fuente | Descripción |
|------|--------|-------------|
| Nodos | OSMnx | Intersecciones de calles (id, lat, lon) |
| Aristas | OSMnx | Segmentos de calle entre intersecciones (geometry LineString, length, name, highway type) |
| Tipo de vía | OSMnx (tag `highway`) | primary, secondary, residential, footway, etc. |

### Datos de contexto urbano a extraer (Overpass API)

| Tag OSM | Qué representa | Query Overpass |
|---------|----------------|----------------|
| `amenity=police` | Comisarías | `node["amenity"="police"](bbox); way["amenity"="police"](bbox);` |
| `highway=street_lamp` | Postes de alumbrado | `node["highway"="street_lamp"](bbox);` |
| `man_made=surveillance` | Cámaras de vigilancia | `node["man_made"="surveillance"](bbox);` |
| `amenity=bank` | Bancos (típicamente con cámaras) | `node["amenity"="bank"](bbox);` |
| `shop=*` | Comercios (indicador de actividad/tránsito) | `node["shop"](bbox);` |

### Criterios de aceptación

| ID | Criterio | Verificación |
|----|----------|-------------|
| CA-08-01 | OSMnx extrae el grafo peatonal de Lima Metropolitana sin errores | El script se ejecuta y retorna un grafo con al menos 50,000 nodos y 60,000 aristas |
| CA-08-02 | Cada arista tiene geometría (LineString), longitud en metros, y tipo de vía | Verificar con `gdf_edges.columns` que contiene 'geometry', 'length', 'highway' |
| CA-08-03 | Los nodos y aristas se insertan en la tabla `street_segments` con geometría PostGIS | Ejecutar `SELECT COUNT(*) FROM street_segments;` debe ser > 50,000. Ejecutar `SELECT ST_AsText(geometry) FROM street_segments LIMIT 1;` debe retornar un LINESTRING válido |
| CA-08-04 | Cada segmento tiene asignado su `district_ubigeo` mediante ST_Within | Ejecutar `SELECT COUNT(*) FROM street_segments WHERE district_ubigeo IS NOT NULL;` debe ser > 95% del total |
| CA-08-05 | La Overpass API retorna datos de comisarías para Lima | Ejecutar query de `amenity=police` con el bounding box; debe retornar al menos 50 resultados |
| CA-08-06 | Los datos de contexto urbano se insertan en la tabla `urban_context` | Para cada segmento, debe existir un registro con: nearby_police_stations (int), lighting_level (estimado), road_type, poi_density |
| CA-08-07 | El campo `nearby_police_stations` se calcula correctamente | Para un segmento cercano a una comisaría conocida (verificar manualmente en el mapa), el valor debe ser >= 1. Para un segmento en zona sin comisaría, debe ser 0 |
| CA-08-08 | El script no falla si la Overpass API no retorna datos para algún tag (ej: pocas cámaras registradas) | Ejecutar con un tag que tenga pocos resultados; el script debe continuar con valor por defecto (0) sin errores |
| CA-08-09 | El script registra su ejecución en `data_load_log` | Registro con source="OSM", timestamps, registros procesados, status |

### Notas para el desarrollador

- OSMnx puede tardar varios minutos para Lima completa. Considerar cachear el grafo en disco después de la primera extracción (`ox.save_graphml()`).
- La cobertura de tags como `highway=street_lamp` y `man_made=surveillance` en OSM para Lima puede ser incompleta. Esto es una limitación conocida. Si un tag no tiene datos suficientes, el factor correspondiente se anula del score (peso = 0) en vez de penalizar.
- El bounding box de Lima Metropolitana debe incluir los 43 distritos. Verificar que distritos periféricos como Ancón (norte), Lurín (sur), Chaclacayo (este) y Callao (oeste, si se incluye) están dentro.
- El tag `highway` de OSMnx diferencia tipos de vía: `primary` y `secondary` son avenidas principales (más tránsito = más seguro), `residential` son calles de barrio, `footway` y `path` son pasajes (potencialmente menos seguros). Esto alimenta el campo `road_type` del contexto urbano.

---

## Resumen de hojas del Excel SIDPOL y su utilidad

| Hoja | Granularidad | Uso en el proyecto |
|------|-------------|-------------------|
| Temp2 | Departamento + tipo general | No usar (muy agregado) |
| Temp3 | Departamento + categoría de delito | No usar (sin distrito) |
| Temp4 | Departamento + modalidad | No usar (sin distrito) |
| **Temp5** | **Distrito + UBIGEO + categoría de delito** | **Fuente principal para RF-07** |
| **Temp5.2** | **Distrito + UBIGEO + modalidad** | **Complemento para RF-12 (ponderación)** |
| Temp6 | Distrito + tipo + subtipo + modalidad (2025) | Alternativa más detallada para RF-12 |
| Temp7 | Distrito + tipo + subtipo + modalidad (2026) | Datos más recientes para RF-12 |