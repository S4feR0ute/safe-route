# SAF-16: Tags de OSM relevantes y sus pesos (RF-08)

Define qué tags de OpenStreetMap se consideran relevantes para el score de contexto urbano, cómo se transforma cada uno en un factor normalizado y qué peso tiene cada factor dentro del `context_score` del segmento. Complementa los criterios de aceptación CA-08 de [SAF-15](SAF-15-criterios-aceptacion-RF07-RF08.md).

## Convención general

- Cada segmento de calle recibe un `context_score` en el rango **[0, 1]**, donde **1 = más riesgoso**. Es la misma convención de la tasa distrital (`district_crime_stats.weighted_crime_rate`, normalizada a [0,1] por el `CrimeAnalyticsService`).
- El `context_score` se calcula como suma ponderada de factores de riesgo:

```
context_score = Σ (w_i × r_i)        con Σ w_i = 1
```

- Cada factor `r_i` está normalizado en [0, 1]. Para los factores **protectores** (iluminación, comisarías, etc.) el riesgo es el complemento de la protección: `r_i = 1 − p_i`.

## Factores, tags y pesos

| # | Factor | Tag(s) OSM | Radio de búsqueda | Peso `w_i` | Tipo |
|---|--------|-----------|-------------------|-----------|------|
| 1 | Iluminación | `highway=street_lamp` | 50 m del segmento | **0.30** | Protector |
| 2 | Presencia policial | `amenity=police` | 300 m / 600 m | **0.20** | Protector |
| 3 | Tipo de vía | `highway=*` (campo `highway_type` del segmento) | — | **0.20** | Riesgo directo |
| 4 | Vigilancia | `man_made=surveillance`, `amenity=bank` | 150 m | **0.15** | Protector |
| 5 | Actividad comercial | `shop=*`, `amenity=restaurant\|cafe\|pharmacy\|marketplace\|fuel` | 100 m | **0.15** | Protector |

La iluminación recibe el mayor peso por ser el factor con mayor correlación documentada con la seguridad peatonal. El tipo de vía aprovecha que `highway_type` ya se persiste para todos los segmentos durante la ingesta del grafo, por lo que es el único factor disponible aunque la extracción Overpass se retrase. Vigilancia y actividad comercial pesan menos porque su cobertura en OSM para ciudades peruanas es más incompleta.

## Normalización de cada factor

### 1. Iluminación (protector, w = 0.30)

```
p_lamp = min(postes_por_100m / 3, 1.0)
r_1 = 1 − p_lamp
```

Un segmento con 3 o más postes (`highway=street_lamp`) por cada 100 m de longitud (`length_m`) se considera totalmente iluminado.

### 2. Presencia policial (protector, w = 0.20)

| Distancia a la comisaría más cercana | `p_police` |
|--------------------------------------|-----------|
| ≤ 300 m | 1.0 |
| ≤ 600 m | 0.5 |
| > 600 m | 0.0 |

`r_2 = 1 − p_police`. Distancia medida con `ST_DWithin` desde la geometría del segmento (usar `geography` para radios en metros reales).

### 3. Tipo de vía (riesgo directo, w = 0.20)

Valor de riesgo `r_3` según `street_segments.highway_type`:

| `highway_type` | `r_3` | Racional |
|---------------|-------|----------|
| `primary`, `primary_link` | 0.20 | Avenidas principales: alto tránsito y visibilidad |
| `secondary`, `secondary_link` | 0.25 | Avenidas secundarias |
| `pedestrian` | 0.30 | Zonas peatonales céntricas, concurridas |
| `tertiary`, `tertiary_link` | 0.35 | Calles colectoras |
| `living_street` | 0.40 | Calles compartidas de barrio |
| `residential` | 0.45 | Calles residenciales, tránsito variable |
| `unclassified` | 0.55 | Vías sin clasificar |
| `service` | 0.60 | Vías de servicio, poco tránsito peatonal |
| `footway`, `steps` | 0.70 | Pasajes peatonales, visibilidad reducida |
| `path` | 0.85 | Senderos informales |
| `track` | 0.90 | Trochas, descampados |
| *(otro / sin dato)* | 0.50 | Valor neutro por defecto |

### 4. Vigilancia (protector, w = 0.15)

```
p_cam = min(elementos_en_150m / 2, 1.0)
r_4 = 1 − p_cam
```

Cuentan tanto cámaras explícitas (`man_made=surveillance`) como bancos (`amenity=bank`), que en la práctica siempre tienen cámaras y vigilancia privada.

### 5. Actividad comercial (protector, w = 0.15)

```
p_poi = min(POIs_en_100m / 5, 1.0)
r_5 = 1 − p_poi
```

Cuentan `shop=*` (cualquier valor) y `amenity` en {`restaurant`, `cafe`, `pharmacy`, `marketplace`, `fuel`}. Cinco o más POIs cercanos indican zona con actividad y "ojos en la calle".

## Regla de cobertura insuficiente

Si tras la ingesta un tag tiene cobertura insuficiente en la ciudad configurada, su factor **se anula (peso = 0) y su peso se redistribuye proporcionalmente** entre los factores restantes, en vez de penalizar a todos los segmentos (regla ya anticipada en las notas de SAF-15).

Umbrales mínimos de cobertura para la ciudad configurada (referencia: Lima Metropolitana + Callao, área de `TARGET_DISTRICTS`):

| Tag | Mínimo de elementos |
|-----|---------------------|
| `highway=street_lamp` | 500 |
| `amenity=police` | 30 |
| `man_made=surveillance` + `amenity=bank` | 100 |
| `shop=*` + amenities listados | 1,000 |

## Tags evaluados y descartados

| Tag | Motivo de descarte |
|-----|--------------------|
| `lit=yes/no` | Cobertura casi nula en Lima; `street_lamp` es mejor proxy |
| `sidewalk=*` | Cobertura muy incompleta e inconsistente |
| `landuse=*`, `leisure=*` | Aporta poco a nivel de segmento en el MVP; candidato post-MVP |
| `maxspeed=*` | Irrelevante para ruteo exclusivamente peatonal |
| `crossing=*` | Relevante para accidentes de tránsito, no para criminalidad |

## Notas para el desarrollador

- Los pesos `w_i`, los radios y los umbrales de cobertura deben ser **configurables** (constantes en `app/core/constants.py`, como ya se hace con `CRIME_WEIGHTS_MAP`), no hardcodeados en la lógica.
- El grafo peatonal debe extraerse con `network_type='walk'`: con `network_type='drive'` no existen segmentos `footway`, `path`, `steps` ni `pedestrian`, que son justamente los tipos de vía con mayor riesgo ponderado en esta definición.
- La extracción Overpass puede hacerse por distrito (mismo patrón de `TARGET_DISTRICTS` usado para el grafo) o por bounding box global; lo relevante es que los conteos por radio se calculen con `ST_DWithin` en PostGIS.
- Los factores alimentan los campos de la tabla `urban_context` (`nearby_police_stations`, `nearby_cameras`, `lighting_level`, `road_type`, `poi_density`); el `context_score` resultante se persiste en `risk_scores.context_score`.
- El peso relativo del `context_score` frente a la capa distrital se define en SAF-43.
