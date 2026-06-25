# SAF-47 — Diseño y Ejecución de Casos de Prueba del Backend (Grafo Sintético + Scores)

**Proyecto:** SafeRoute Lima
**Responsable QA:** Anngie Salazar Alvarez

## ¿Qué estamos probando?

El ticket pide verificar el cálculo del `composite_score` (la fórmula que decide qué tan riesgosa es una calle), definida en `ScoreCalculatorService` (SAF-43):

```
composite_score = 0.70 * district_score + 0.30 * context_score
context_score   = 0.30*r_lighting + 0.20*r_police + 0.20*r_road + 0.15*r_cameras + 0.15*r_commerce
```

En lugar de usar los 808,200 segmentos reales de Lima (imposible de verificar a mano), insertamos un **grafo sintético**: unas pocas calles de prueba con datos que nosotros elegimos, ubicadas en coordenadas (0°, 0°) que no existen en los datos reales de Lima (para no mezclarlas con nada real). Así sabemos de antemano cuál debería ser el resultado exacto, y lo comparamos con lo que realmente calcula el sistema.

**Nota importante:** los factores de iluminación (`r_lighting`) y comercio (`r_commerce`) todavía no están implementados en el código (siempre usan el valor neutro 0.5, según los comentarios en `score_calculator_service.py`). Por eso estos casos no los prueban — solo lo que sí está construido.

---

### CP-B01 — Score correcto en distrito de alta criminalidad

| Campo | Detalle |
|---|---|
| **Precondiciones** | Datos sintéticos TC1 insertados (distrito `999901`, criminalidad 0.90; vía tipo `path`; sin comisaría ni cámaras cerca). |
| **Pasos** | 1. Ejecutar `python -m app.data_loader.calculate_scores`.<br>2. Consultar `SELECT district_score, context_score, composite_score FROM risk_scores WHERE segment_id = 9000001;` |
| **Resultado esperado** | `district_score = 0.90`, `context_score = 0.745`, `composite_score = 0.8535` |
| **Resultado obtenido** |El sistema calculó district_score = 0.9, context_score = 0.745, composite_score = 0.8535, coincidiendo exactamente con el valor esperado. |
| **Estado** | PASS|

### CP-B02 — Score correcto en distrito de baja criminalidad con buena infraestructura

| Campo | Detalle |
|---|---|
| **Precondiciones** | Datos sintéticos TC2 insertados (distrito `999902`, criminalidad 0.10; vía `primary`; comisaría a ~55m; 2 cámaras a menos de 150m). |
| **Pasos** | 1. (Mismo cálculo ya ejecutado en CP-B01, no hay que repetirlo).<br>2. Consultar `SELECT district_score, context_score, composite_score FROM risk_scores WHERE segment_id = 9000002;` |
| **Resultado esperado** | `district_score = 0.10`, `context_score = 0.265`, `composite_score = 0.1495` |
| **Resultado obtenido** | El sistema calculó district_score = 0.1, context_score = 0.265, composite_score = 0.1495, coincidiendo exactamente con el valor esperado.|
| **Estado** | PASS|

### CP-B03 — Distrito sin datos de criminalidad usa el valor neutro (0.5)

| Campo | Detalle |
|---|---|
| **Precondiciones** | Segmento sintético TC3 con `district_ubigeo = '999903'`, código que NO existe en `district_crime_stats` a propósito. |
| **Pasos** | Consultar `SELECT district_score, context_score, composite_score FROM risk_scores WHERE segment_id = 9000003;` |
| **Resultado esperado** | `district_score = 0.5` (valor neutro, `SCORE_NEUTRO`), `context_score = 0.665`, `composite_score = 0.5495` |
| **Resultado obtenido** |El sistema calculó district_score = 0.5, context_score = 0.665, composite_score = 0.5495, confirmando que usa correctamente el valor neutro cuando el distrito no tiene datos de criminalidad. |
| **Estado** |  PASS|

### CP-B04 — Factor de policía en distancia intermedia (300–600m)

| Campo | Detalle |
|---|---|
| **Precondiciones** | Segmento sintético TC4 con una comisaría de prueba a ~450m (banda intermedia). |
| **Pasos** | Consultar `SELECT context_score, composite_score FROM risk_scores WHERE segment_id = 9000004;` |
| **Resultado esperado** | `context_score = 0.565`, `composite_score = 0.5195` (corresponde a `r_police = 0.5`) |
| **Resultado obtenido** |El sistema calculó context_score = 0.565, composite_score = 0.5195, coincidiendo exactamente. |
| **Estado** | PASS|

### CP-B05 — Factor de cámaras con exactamente 1 cámara cercana

| Campo | Detalle |
|---|---|
| **Precondiciones** | Segmento sintético TC5 con exactamente 1 cámara a menos de 150m. |
| **Pasos** | Consultar `SELECT context_score, composite_score FROM risk_scores WHERE segment_id = 9000005;` |
| **Resultado esperado** | `context_score = 0.59`, `composite_score = 0.527` (corresponde a `r_cameras = 0.5`) |
| **Resultado obtenido** |El sistema calculó context_score = 0.59, composite_score = 0.527, coincidiendo exactamente. |
| **Estado** | PASS|

---

## Registro de defectos encontrados

Sin defectos encontrados.

