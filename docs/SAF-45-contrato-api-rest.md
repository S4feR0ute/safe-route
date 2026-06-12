# SAF-45: Contrato de API REST — endpoints, schemas y códigos de error (RF-01 a RF-06)

Define el contrato entre el frontend y la API de ruteo: endpoints, formatos de request/response y códigos de error. Cubre RF-01 a RF-06. Los endpoints de autenticación y reportes ciudadanos (RF-13 a RF-19) se contratarán en sus propios tickets (Sprint 5).

Escalas y semántica de los valores devueltos: ver [SAF-43](SAF-43-pesos-capas-scoring.md) (scores) y [SAF-44](SAF-44-umbrales-categorias.md) (categorías y colores).

## Convenciones generales

| Convención | Definición |
|------------|------------|
| Base path | `/api/v1` (versionado en URL) |
| Formato | JSON (`Content-Type: application/json`), UTF-8 |
| Coordenadas | Objetos `{"lat": float, "lon": float}` en WGS84 (SRID 4326). En GeoJSON, los pares siguen el estándar `[lon, lat]` |
| Autenticación | Los endpoints de este contrato son **públicos** (RU-05: la consulta de rutas no requiere registro). El middleware JWT existente aplica a endpoints futuros de moderación/reportes |
| Stateless | Ningún endpoint mantiene sesión (RD-02) |
| CORS | Habilitado para el origen del frontend (configurable por entorno) |
| Idioma | Mensajes de error orientados al usuario en español; `code` de error en inglés y estable (es lo que el frontend usa para decidir) |

## Formato de error uniforme

Todas las respuestas con status ≥ 400 usan el mismo schema:

```json
{
  "error": {
    "code": "NO_ROUTE_FOUND",
    "message": "No existe una ruta peatonal entre los puntos indicados.",
    "details": {}
  }
}
```

- `code`: identificador estable en MAYÚSCULAS_CON_GUIONES; el frontend decide por este campo, nunca por `message`.
- `message`: texto mostrable al usuario.
- `details`: objeto opcional con contexto (campo inválido, valores recibidos, etc.).

> Nota de implementación: FastAPI responde 422 con su propio formato para errores de validación de Pydantic. Debe registrarse un exception handler que lo convierta a este schema con `code = "VALIDATION_ERROR"`.

## Endpoints

### 1. `GET /api/v1/health`

Verificación de vida del servicio (usado por Docker healthcheck y monitoreo).

**Response 200:**

```json
{ "status": "ok", "database": "ok" }
```

**Response 503:** `database: "unavailable"` si la BD no responde (con el formato de error uniforme).

---

### 2. `POST /api/v1/route` — RF-01, RF-03, RF-04, RF-05, RF-11

Calcula la ruta peatonal más segura entre origen y destino y, opcionalmente, la más corta para comparación.

**Request body:**

```json
{
  "origin":      { "lat": -12.0464, "lon": -77.0428 },
  "destination": { "lat": -12.1211, "lon": -77.0297 },
  "include_shortest": true
}
```

| Campo | Tipo | Obligatorio | Validación |
|-------|------|-------------|------------|
| `origin`, `destination` | objeto coord | Sí | `lat` ∈ [-90, 90], `lon` ∈ [-180, 180]; dentro del área de cobertura de la ciudad configurada |
| `include_shortest` | boolean | No (default `true`) | Si es `false`, `shortest_route` y `comparison` llegan como `null` |

Reglas adicionales: origen ≠ destino (tolerancia 50 m); distancia en línea recta ≤ 15 km (límite razonable de caminata, configurable).

**Response 200:**

```json
{
  "safe_route": {
    "summary": {
      "distance_m": 5420,
      "walk_time_min": 65,
      "security_score": 78,
      "category": "Segura"
    },
    "geojson": {
      "type": "FeatureCollection",
      "features": [
        {
          "type": "Feature",
          "geometry": { "type": "LineString", "coordinates": [[-77.0428, -12.0464], [-77.0431, -12.0470]] },
          "properties": {
            "segment_id": 12345,
            "name": "Av. Arequipa",
            "length_m": 85.2,
            "risk_score": 0.21,
            "color": "#2E7D32"
          }
        }
      ]
    }
  },
  "shortest_route": { "summary": { "...": "mismo schema que safe_route" }, "geojson": { "...": "..." } },
  "comparison": {
    "extra_distance_m": 480,
    "extra_time_min": 6,
    "risk_reduction_pct": 35
  }
}
```

Decisiones de diseño del response:

- **Un Feature por segmento** (no una sola LineString): permite al frontend colorear cada tramo según riesgo (RF-03) pasando el GeoJSON directo a Leaflet, sin lógica adicional.
- **`category` y `color` vienen resueltos por el backend** según los umbrales de SAF-44; el frontend no duplica esa lógica.
- `walk_time_min` se calcula con velocidad peatonal de **5 km/h** (≈ 83 m/min), redondeado a entero.
- `risk_reduction_pct` = reducción porcentual del riesgo promedio de la ruta segura respecto a la corta.

**Errores:**

| Status | `code` | Cuándo |
|--------|--------|--------|
| 400 | `INVALID_COORDINATES` | lat/lon fuera de rango, origen = destino, o distancia > límite |
| 400 | `OUT_OF_COVERAGE` | Punto fuera del área de la ciudad configurada |
| 404 | `NO_ROUTE_FOUND` | El grafo no conecta origen y destino (p. ej. punto en isla o zona sin calles) |
| 422 | `VALIDATION_ERROR` | Body malformado o campos faltantes (handler sobre el 422 de FastAPI) |
| 429 | `RATE_LIMITED` | Reservado: se activará junto con el rate limiting de reportes (Sprint 5) |
| 500 | `INTERNAL_ERROR` | Error no controlado; sin detalles internos en la respuesta (OWASP) |
| 503 | `SERVICE_UNAVAILABLE` | BD no disponible o scores aún no calculados |

---

### 3. Geocodificación (RF-06)

La geocodificación del MVP se resuelve en el **frontend, directo contra Nominatim** (implementado en la story de búsqueda de direcciones), con estos parámetros contractuales:

```
GET https://nominatim.openstreetmap.org/search
    ?q={texto}&format=json&limit=5&countrycodes=pe
    &viewbox={bbox_ciudad}&bounded=1
```

- `viewbox` debe corresponder al **bounding box completo de la ciudad configurada**. Para Lima Metropolitana + Callao: `-77.20,-11.57,-76.62,-12.52` (oeste, norte, este, sur según SAF-15).
  - ⚠️ El valor actualmente en el frontend (`-77.2,-11.8,-76.8,-12.2`) cubre solo el área central: deja fuera Ancón, Carabayllo, Lurín, Pucusana, Chaclacayo y otros distritos periféricos. Debe corregirse a la caja completa.
- Se respeta la política de uso de Nominatim: máximo 1 request/segundo (el debounce de 300 ms del frontend más la espera de tipeo lo cumple en la práctica) y `User-Agent`/`Referer` identificable.
- Si el array de resultados llega vacío, el frontend muestra "Dirección no encontrada" (no es un error del API propio).

> Post-MVP: si Nominatim aplica límites de uso o se necesita auditoría, se introducirá `GET /api/v1/geocode?q=` como proxy del backend manteniendo el mismo shape de respuesta hacia el frontend.

## Mapa de requisitos a contrato

| RF | Cobertura en este contrato |
|----|---------------------------|
| RF-01 Consultar ruta segura | `POST /api/v1/route` (request origen/destino, response `safe_route`) |
| RF-02 Seleccionar puntos en mapa | El mapa produce coords `{lat, lon}` que alimentan el mismo request |
| RF-03 Visualizar ruta con colores | GeoJSON por segmento con `risk_score` y `color` |
| RF-04 Mostrar score y categoría | `summary.security_score` + `summary.category` |
| RF-05 Comparar segura vs. corta | `shortest_route` + `comparison` |
| RF-06 Geocodificar direcciones | Integración Nominatim del frontend (sección 3) |

## Notas para el desarrollador

- El frontend hoy maneja coordenadas como arrays `[lat, lon]` (estado de React y eventos de Leaflet); al implementar la conexión con el API debe transformarlas al objeto `{lat, lon}` del contrato. Se eligió el objeto explícito para eliminar la ambigüedad de orden lat/lon entre Leaflet (lat primero) y GeoJSON (lon primero).
- El límite de cobertura (`OUT_OF_COVERAGE`) se valida contra la unión de los distritos cargados (o su bounding box, más simple para el MVP), no contra una constante separada que pueda divergir de los datos.
- Mantener este documento como fuente de verdad del contrato hasta que exista el OpenAPI generado por FastAPI; a partir de ahí, `/docs` (Swagger) es la referencia viva y este documento conserva las decisiones de diseño.
