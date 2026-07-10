# SafeRoute — Requisitos Funcionales Implementados

Anexo del SRS que resume el estado de implementación de cada requisito funcional del sistema.

## Resumen

De los 19 requisitos funcionales, 16 están implementados por completo y 3 se encuentran parcialmente implementados: la comparación visual de rutas en la interfaz (RF-05), la ejecución programada del cargador de datos (RF-10) y la diferenciación de reportes verificados en el mapa (RF-19).

## Detalle por requisito

| RF | Nombre | Estado | Componente principal |
| --- | --- | --- | --- |
| RF-01 | Consultar ruta segura | Implementado | `api/route_endpoint.py`, `services/routing_service.py` |
| RF-02 | Seleccionar puntos en el mapa | Implementado | `components/MapView.jsx`, `pages/MapPage.jsx` |
| RF-03 | Visualizar ruta con colores por riesgo | Implementado | `routing_service` (GeoJSON con color por segmento) |
| RF-04 | Mostrar score (número y categoría) | Implementado | `routing_service`, `components/ResultsPanel.jsx` |
| RF-05 | Comparar ruta segura vs. corta | Parcial | Backend completo; la interfaz aún no muestra la comparación |
| RF-06 | Geocodificar direcciones | Implementado | `api/geocode_endpoint.py`, `services/nominatim_service.py` |
| RF-07 | Ingestar datos de criminalidad | Implementado | `data_loader/ingest_sidpol.py`, `services/crime_analytics_service.py` |
| RF-08 | Ingestar grafo y contexto urbano | Implementado | `data_loader/ingest_street_graph.py`, `ingest_urban_context.py` |
| RF-09 | Calcular score compuesto (3 capas) | Implementado | `services/score_calculator_service.py` |
| RF-10 | Ejecutar cálculo programado | Parcial | Orquestador manual por CLI; sin scheduler automático |
| RF-11 | Calcular ruta óptima (Dijkstra ponderado) | Implementado | `routing_service.calculate_routes` |
| RF-12 | Ponderar por tipo de delito | Implementado | `core/constants.py`, `crime_analytics_service.py` |
| RF-13 | Gestionar cuentas de usuario (JWT) | Implementado | `api/auth_endpoint.py`, `core/security.py` |
| RF-14 | Reporte rápido sin cuenta (modo 1) | Implementado | `api/report_endpoints.py`, rate limiting en middleware |
| RF-15 | Reporte con cuenta (modo 2) | Implementado | `services/report_service.py` |
| RF-16 | Reporte con documentos (modo 3) | Implementado | `report_endpoints`, `services/file_storage_service.py` |
| RF-17 | Validar reportes documentados | Implementado | `api/moderation_endpoints.py`, `pages/ModerationPage.jsx` |
| RF-18 | Incorporar reportes verificados al score | Implementado | `score_calculator_service` (`ST_DWithin`, peso y decaimiento) |
| RF-19 | Visualizar reportes en el mapa | Parcial | Endpoint y marcadores listos; falta afinar la diferenciación verificado/no verificado |

## Observaciones sobre los requisitos parciales

- **RF-05:** el backend ya devuelve la ruta segura, la ruta corta y su comparación en una sola respuesta; resta mostrar la comparación en la interfaz.
- **RF-10:** la ingesta y el cálculo se ejecutan mediante un orquestador por línea de comandos; queda pendiente automatizar su ejecución periódica.
- **RF-19:** los reportes se muestran en el mapa; falta consolidar la distinción visual entre reportes verificados y no verificados.
