# SAF-44: Umbrales de categorías del score de seguridad (RF-04)

Define los umbrales que convierten el score numérico de una ruta en su categoría cualitativa (**Segura**, **Moderada**, **Riesgosa**) y los colores de riesgo por segmento (RF-03). Depende de las escalas definidas en [SAF-43](SAF-43-pesos-capas-scoring.md): riesgo por segmento `composite_score` en [0,1] (1 = más riesgoso) y score global de ruta `security_score` en 0–100 (mayor = más seguro).

## Categorías de la ruta (RF-04)

Sobre `security_score` (0–100):

| Categoría | Rango | Color asociado |
|-----------|-------|----------------|
| **Segura** | 70 – 100 | Verde |
| **Moderada** | 40 – 69 | Ámbar |
| **Riesgosa** | 0 – 39 | Rojo |

### Regla de degradación

Una ruta **no puede categorizarse como "Segura" si más del 10% de su longitud** corresponde a segmentos rojos (riesgo alto), aunque su promedio supere 70. En ese caso se degrada a **Moderada**. Evita que un promedio alto oculte un tramo peligroso concentrado.

## Colores por segmento (RF-03)

Sobre `composite_score` del segmento ([0,1]):

| Color | Rango de `composite_score` | Nivel |
|-------|---------------------------|-------|
| **Verde** | 0.00 – 0.30 | Riesgo bajo |
| **Amarillo** | > 0.30 – 0.60 | Riesgo medio |
| **Rojo** | > 0.60 – 1.00 | Riesgo alto |

Los cortes por segmento (0.30 / 0.60) son los complementos de los cortes de categoría (70 / 40 en escala 0–100), de modo que ambas escalas cuentan la misma historia: una ruta compuesta solo por segmentos verdes siempre es "Segura" y una compuesta solo por rojos siempre es "Riesgosa".

## Justificación y calibración

- Los cortes iniciales (terciles desplazados: 0.30 / 0.60 en vez de 0.33 / 0.66) son **deliberadamente conservadores**: es preferible subestimar la seguridad de una ruta que sobreestimarla, dado que el costo de un falso "Segura" lo asume el peatón.
- Con la normalización min-max de la capa distrital (los distritos extremos anclan 0 y 1), la mayoría de segmentos caerá en valores intermedios; los umbrales deben **recalibrarse con la distribución real** tras la primera carga completa de scores: QA reporta la distribución de `composite_score` por percentiles y BA ajusta los cortes si más del 80% de los segmentos cae en una sola banda.
- Cualquier ajuste cambia solo constantes de configuración, no lógica.

## Presentación al usuario (RF-04, RU-04)

- El panel de resultados muestra **siempre número y categoría juntos**: `78 / 100 — Segura`. La categoría nunca se comunica solo con color (accesibilidad para daltonismo, RU-04).
- `security_score` se muestra redondeado a entero, sin decimales.
- Colores recomendados (distinguibles para los tipos comunes de daltonismo y con contraste AA sobre fondo de mapa):

| Uso | Color | Hex |
|-----|-------|-----|
| Verde (bajo / Segura) | Verde oscuro | `#2E7D32` |
| Amarillo (medio / Moderada) | Ámbar | `#F9A825` |
| Rojo (alto / Riesgosa) | Rojo oscuro | `#C62828` |

- Los colores de segmentos de ruta deben distinguirse de los marcadores de origen (verde) y destino (rojo) ya usados en el mapa: los segmentos se dibujan como líneas con grosor ≥ 5px y opacidad ~0.8, no como marcadores.
- En la comparación ruta segura vs. corta (RF-05), ambas rutas muestran su propio score y categoría con esta misma escala.

## Casos borde

| Caso | Regla |
|------|-------|
| Score exactamente en el corte (70 o 40) | Pertenece a la categoría superior (los rangos son inclusivos en el límite inferior: Segura = [70, 100]) |
| Ruta de un solo segmento | Aplica la misma fórmula (el promedio ponderado equivale al score del segmento) |
| Segmentos sin score pre-calculado en `risk_scores` | Se tratan como riesgo neutro (0.5 → amarillo) y se registra advertencia; no deben bloquear la respuesta |

## Notas para el desarrollador

- Umbrales (70/40 y 0.30/0.60), regla de degradación (10%) y colores hex deben ser **constantes de configuración** compartidas: backend (categoría en la respuesta del API) y frontend (colores de render). El contrato del API (SAF-45) devuelve categoría y color ya resueltos por el backend para evitar duplicar esta lógica en el frontend.
- Las categorías en la respuesta del API se serializan como `"Segura" | "Moderada" | "Riesgosa"` (en español, tal como se muestran al usuario).
