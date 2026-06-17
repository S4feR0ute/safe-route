# SAF-37 — Aplicación de principios SOLID en el backend

Documento que mapea dónde se aplica cada principio SOLID en el backend (`backend/app`) y registra el refactor realizado en este ticket.

## Resumen

| Principio | Estado | Dónde |
| --- | --- | --- |
| SRP | Aplicado | Un servicio/repositorio por responsabilidad |
| OCP | Parcial | Interfaces de DAOs extensibles; algunos pesos aún hardcodeados |
| LSP | Aplicado | Las implementaciones respetan el contrato de sus interfaces |
| ISP | Aplicado | Interfaces pequeñas y cohesivas por fuente de datos |
| DIP | Aplicado | Dependencias (Session, DAOs) inyectadas vía abstracciones |

## SRP — Responsabilidad única

Cada servicio tiene una sola razón para cambiar:

- `services/routing_service.py` → `RoutingService`: solo ejecuta el ruteo (Dijkstra ponderado).
- `services/score_calculator_service.py` → `ScoreCalculatorService`: solo calcula el score compuesto.
- `services/crime_analytics_service.py` → `CrimeAnalyticsService`: solo normaliza estadísticas de criminalidad.
- `services/segment_district_service.py` → `SegmentDistrictService`: solo asigna distrito a segmentos (ST_Within).
- `repositories/osmnx_street_graph_dao.py` → `OSMnxStreetGraphDAO`: solo extrae/persiste el grafo vial.

## OCP — Abierto/cerrado

Las interfaces de `interfaces/` permiten agregar nuevas fuentes sin modificar a los consumidores:

- `interfaces/crime_interface.py` → `ICrimeRepository`: se puede añadir otra fuente de crimen sin tocar al consumidor (impl. actual `repositories/sidpol_repository.py`).
- `interfaces/street_graph_interface.py` → `IStreetGraphDAO`: se puede añadir otra fuente de grafo sin tocar `RoutingService`.

Pendiente (ver "Mejoras futuras"): los factores del `context_score` en `ScoreCalculatorService` y los umbrales de color en `api/route_endpoint.py` aún están hardcodeados.

## LSP — Sustitución de Liskov

Las implementaciones concretas son sustituibles por su abstracción sin romper el contrato:

- `SIDPOLCrimeRepository` ⟶ `ICrimeRepository`
- `OSMnxStreetGraphDAO` ⟶ `IStreetGraphDAO`
- `OSMnxContextDAO` ⟶ `IUrbanContextDAO`
- `OSMnxDistrictDAO` ⟶ `IDistrictDAO`

## ISP — Segregación de interfaces

Las interfaces son pequeñas y específicas por fuente de datos (`interfaces/`): `ICrimeRepository`, `IStreetGraphDAO`, `IUrbanContextDAO`, `IDistrictDAO`. Ningún implementador queda obligado a definir métodos que no usa.

## DIP — Inversión de dependencias

- Los servicios reciben `Session` (abstracción de SQLAlchemy) por constructor, no una conexión concreta.
- Los endpoints obtienen la sesión vía `Depends(get_db)` (`api/route_endpoint.py`, `api/geocode_endpoint.py`); no instancian la BD.
- **Refactor de este ticket:** `RoutingService` dependía directamente de la implementación concreta `OSMnxStreetGraphDAO`. Ahora depende de la abstracción `IStreetGraphDAO`, inyectable por constructor con un valor por defecto que conserva el comportamiento actual. Beneficio adicional: permite inyectar un grafo sintético en los tests del backend.

```python
def __init__(self, db: Session, graph_dao: IStreetGraphDAO = None):
    self.db = db
    self._graph_dao = graph_dao  # default: OSMnxStreetGraphDAO
```

## Mejoras futuras (backlog)

- **OCP** en `ScoreCalculatorService`: extraer los factores de contexto a una abstracción (`IContextFactor`) e inyectar la lista, para añadir factores sin modificar el servicio.
- **DIP/LSP** en geocodificación: definir `IGeocoder` e implementarla en `NominatimService` para poder sustituir el proveedor.
- **OCP** en `api/route_endpoint.py`: mover los umbrales/colores de riesgo a configuración o a un servicio dedicado.
