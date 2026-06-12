# SAF-43: Pesos relativos de cada capa en la fórmula de scoring (RF-09)

Define cómo se combinan las capas del score de riesgo compuesto por segmento, qué peso tiene cada una y cómo se incorpora el score al costo del ruteo (RF-11). Las definiciones de cada capa individual están en sus propios documentos: capa distrital en [SAF-15](SAF-15-criterios-aceptacion-RF07-RF08.md) (RF-07) y capa de contexto urbano en [SAF-16](SAF-16-tags-osm-pesos.md) (RF-08).

## Capas del score

| Capa | Variable | Rango | Fuente | Definición |
|------|----------|-------|--------|------------|
| 1. Criminalidad distrital | `district_score` | [0, 1] | SIDPOL (tabla `district_crime_stats`) | Es directamente `weighted_crime_rate` del distrito del segmento, ya normalizado a [0,1] por el `CrimeAnalyticsService` (ponderación por tipo de delito con `CRIME_WEIGHTS_MAP`, raíz cuadrada para amortiguar outliers y min-max sobre los distritos de la ciudad) |
| 2. Contexto urbano | `context_score` | [0, 1] | OSM/Overpass (tabla `urban_context`) | Suma ponderada de 5 factores definida en SAF-16 |
| 3. Reportes verificados | `report_score` | [0, 1] | Reportes ciudadanos modo 3 validados (RF-18, Sprint 6) | Por definir en el ticket de RF-18; reservada en la fórmula desde ya |

En todas las capas **1 = más riesgoso**.

## Fórmula del score compuesto

```
composite_score = w_d × district_score + w_c × context_score + w_r × report_score
```

con `w_d + w_c + w_r = 1`.

### Pesos vigentes (MVP, dos capas)

Mientras RF-18 no esté implementado, `report_score = 0` y los pesos son:

| Peso | Valor |
|------|-------|
| `w_d` (distrital) | **0.70** |
| `w_c` (contexto urbano) | **0.30** |
| `w_r` (reportes) | 0.00 |

### Pesos con la tercera capa activa (Sprint 6, RF-18)

| Peso | Valor |
|------|-------|
| `w_d` (distrital) | **0.60** |
| `w_c` (contexto urbano) | **0.25** |
| `w_r` (reportes) | **0.15** |

### Justificación

- **La capa distrital domina (0.70 / 0.60):** es la única fuente oficial de criminalidad disponible (SIDPOL); su limitación es la granularidad (distrito), no la confiabilidad.
- **El contexto urbano corrige a nivel de calle (0.30 / 0.25):** diferencia segmentos dentro de un mismo distrito (una avenida iluminada vs. un pasaje), pero proviene de datos voluntarios de OSM con cobertura desigual, por lo que no debe superar a la capa oficial.
- **Los reportes verificados tienen peso acotado (0.15):** el SRS §1.3.4 exige que esta capa tenga "un peso acotado y configurable" mientras el volumen de reportes sea bajo. Podrá revisarse cuando exista masa crítica de reportes validados.

## Casos borde

| Caso | Regla |
|------|-------|
| Segmento sin `district_ubigeo` asignado (ST_Within no lo ubicó en ningún distrito) | `district_score = 0.5` (valor neutro) |
| Segmento sin registro en `urban_context` | `context_score` se calcula solo con el factor tipo de vía (disponible en `street_segments.highway_type`), según SAF-16 |
| Distrito sin datos en `district_crime_stats` | `district_score = 0.5` y se registra advertencia en el log de carga |

## Incorporación al costo de ruteo (RF-11)

El Dijkstra ponderado no debe optimizar solo riesgo (produciría rutas absurdamente largas) ni solo distancia. El costo de cada arista es:

```
cost(e) = length_m × (1 + α × composite_score)
```

- **`α = 2.0`** (factor de aversión al riesgo, configurable).
- Interpretación: un segmento con riesgo máximo (1.0) "cuesta" 3 veces su longitud real; un segmento con riesgo 0 cuesta su longitud.
- Para la **ruta más corta** (RF-05) se usa `cost(e) = length_m` (α = 0) sobre el mismo grafo.
- Criterio de calibración: con α = 2.0 la ruta segura no debería exceder en más de ~40% la longitud de la ruta corta en consultas típicas. Si en pruebas reales se excede sistemáticamente, ajustar α hacia abajo (QA reporta, BA decide).

## Score global de la ruta

El score que se muestra al usuario (RF-04) se calcula como promedio del riesgo ponderado por longitud de los segmentos de la ruta:

```
risk_route = Σ (length_i × composite_i) / Σ length_i
security_score = round(100 × (1 − risk_route))
```

`security_score` está en escala **0–100, donde mayor = más seguro**. Los umbrales de categorías (Segura, Moderada, Riesgosa) sobre esta escala se definen en SAF-44.

## Persistencia

Los scores se pre-calculan (RD-05) y persisten en la tabla `risk_scores` (SRS §3.5):

| Campo | Contenido |
|-------|-----------|
| `segment_id` | FK a `street_segments` |
| `district_score` | Capa 1 del segmento |
| `context_score` | Capa 2 del segmento |
| `report_score` | Capa 3 (0 hasta RF-18) |
| `composite_score` | Resultado de la fórmula con los pesos vigentes |
| `last_updated` | Timestamp del último cálculo |

## Notas para el desarrollador

- Los pesos `w_d`, `w_c`, `w_r` y el factor `α` deben ser **configurables** (constantes en `app/core/constants.py` o variables de entorno), de modo que activar la tercera capa en el Sprint 6 sea un cambio de configuración, no de código.
- El Score Calculator debe ser testeable con datos sintéticos (SRS §3.7): con tasas, contexto y pesos conocidos, el `composite_score` esperado se verifica a mano (criterio de verificación de RF-09/RF-12).
- No recalcular `weighted_crime_rate` en el Score Calculator: leerla de `district_crime_stats`, que es la salida ya normalizada del `CrimeAnalyticsService`.
