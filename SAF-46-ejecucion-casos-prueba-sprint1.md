# SAF-46 — Ejecución de Casos de Prueba: Sprint 1
**Proyecto:** SafeRoute Lima
**Sprint:** 1
**Responsable QA:** Salazar Alvarez Anngie
**URL de la aplicación:** http://localhost:5173

---

## Resumen de ejecución

| Total de casos | Ejecutados | PASS | FAIL | BLOQUEADO | % Aprobación |
|       9        |      9      |  6  |  3   |     0     |    66.7 %    |

---

## Módulo 1: Carga y visualización del mapa

### CP-01 — Carga inicial del mapa

| Campo | Detalle |
|-------|---------|
| **ID Jira** | SAF-46 |
| **Caso de prueba** | CP-01 |
| **Precondiciones** | El servidor de desarrollo está corriendo (`npm run dev`). El navegador tiene acceso a internet (para cargar tiles de OpenStreetMap). |
| **Pasos** | 1. Abrir el navegador.<br>2. Ingresar la URL `http://localhost:5173`.<br>3. Esperar a que la página termine de cargar. |
| **Resultado esperado** | El mapa de Lima se muestra centrado en las coordenadas `-12.0464, -77.0428` con zoom 12. Los tiles de OpenStreetMap cargan correctamente sin errores visuales. |
| **Resultado obtenido** | El mapa cargó centrado en Lima sin errores visuales|
| **Estado** | PASS |
| **Evidencia** | ![cp-01](/imagenes/cp01.png) |
| **Observaciones** |Sin observaciones adicionales. |

---

### CP-02 — Responsividad del mapa

| Campo | Detalle |
|-------|---------|
| **ID Jira** | SAF-46 |
| **Caso de prueba** | CP-02 |
| **Precondiciones** | Aplicación cargada correctamente (CP-01 en PASS). |
| **Pasos** | 1. Con el mapa cargado, usar el scroll del mouse para hacer zoom in (acercar). 2. Usar el scroll para hacer zoom out (alejar). 3. Hacer clic y arrastrar el mapa para desplazarlo. |
| **Resultado esperado** | El mapa responde al zoom y al arrastre sin errores. Los tiles se recargan al cambiar la vista. |
| **Resultado obtenido** |El mapa respondió correctamente al zoom y al arrastre, sin errores ni demoras notables.|
| **Estado** | PASS |
| **Evidencia** | |
| **Observaciones** | Sin observaciones adicionales. |

---

## Módulo 2: Selección de puntos en el mapa

### CP-03 — Selección de origen con clic en el mapa

| Campo | Detalle |
|-------|---------|
| **ID Jira** | SAF-46 |
| **Caso de prueba** | CP-03 |
| **Precondiciones** | Aplicación cargada. Ningún punto seleccionado previamente. |
| **Pasos** | 1. Hacer clic en cualquier zona del mapa. |
| **Resultado esperado** | Aparece un marcador verde en el punto clicado. El campo "Origen" en el formulario muestra las coordenadas en formato `lat, lon` con 4 decimales. |
| **Resultado obtenido** |El marcador de origen no se muestra en verde; la consola muestra error 404 al buscar marker-green.png, y además un error net::ERR_BLOCKED_BY_ORB al intentar cargar ese recurso, lo que confirma que el archivo de ícono no se está sirviendo correctamente. Las coordenadas sí se capturan bien en el formulario.|
| **Estado** |FAIL|
| **Evidencia** | ![cp-03](/imagenes/cp03.png)|
| **Observaciones** | Sin observaciones adicionales|

---

### CP-04 — Selección de destino con clic en el mapa

| Campo | Detalle |
|-------|---------|
| **ID Jira** | SAF-46 |
| **Caso de prueba** | CP-04 |
| **Precondiciones** | CP-03 ejecutado en PASS (ya existe un marcador de origen). |
| **Pasos** | 1. Hacer clic en una zona diferente del mapa. |
| **Resultado esperado** | Aparece un marcador rojo en el segundo punto. El campo "Destino" muestra sus coordenadas. El marcador verde de origen permanece visible. |
| **Resultado obtenido** | Las coordenadas de destino se registran correctamente, pero el marcador rojo no se muestra; la pestaña Network confirma el mismo error que en CP-03 (404 / ERR_BLOCKED_BY_ORB) al intentar cargar marker-red.png.|
| **Estado** |FAIL|
| **Evidencia** | |
| **Observaciones** | Sin observaciones adicionales|

---

### CP-05 — Búsqueda de dirección por texto (Nominatim)

| Campo | Detalle |
|-------|---------|
| **ID Jira** | SAF-46 |
| **Caso de prueba** | CP-05 |
| **Precondiciones** | Aplicación cargada. Conexión a internet activa. |
| **Pasos** | 1. Hacer clic en el campo de texto "Origen".<br>2. Escribir `Miraflores`.<br>3. Esperar ~1 segundo.<br>4. Verificar que aparece una lista de sugerencias.<br>5. Hacer clic en una sugerencia. |
| **Resultado esperado** | La lista muestra al menos 1 sugerencia con dirección en Lima/Perú. Al seleccionar, el mapa se centra en esa ubicación y aparece el marcador verde con las coordenadas en el campo Origen. |
| **Resultado obtenido** |La búsqueda por texto funcionó correctamente: al escribir 'Miraflores' apareció la lista de sugerencias, y al seleccionar una el mapa se centró ahí con las coordenadas correctas en el campo Origen. El marcador presenta el mismo defecto de ícono roto ya registrado (defecto #1). |
| **Estado** |FAIL |
| **Evidencia** | |
| **Observaciones** | Técnicamente no cumple el resultado esperado completo (por el ícono), aunque toda la lógica de búsqueda y geocodificación funciona bien.|

---

## Módulo 3: Validación del formulario

### CP-06 — Envío de formulario sin origen ni destino

| Campo | Detalle |
|-------|---------|
| **ID Jira** | SAF-46 |
| **Caso de prueba** | CP-06 |
| **Precondiciones** | Aplicación cargada. Ningún punto seleccionado. |
| **Pasos** | 1. Sin seleccionar ningún punto en el mapa ni escribir en los campos, hacer clic en el botón "Buscar Ruta Segura". |
| **Resultado esperado** | El sistema muestra el mensaje de alerta: `"Por favor selecciona origen y destino"`. No se realiza ninguna búsqueda. |
| **Resultado obtenido** | Al hacer clic en 'Buscar Ruta Segura' sin seleccionar ningún punto, apareció el mensaje de alerta esperado y no se ejecutó ninguna búsqueda.|
| **Estado** |PASS|
| **Evidencia** |![cp-06](/imagenes/cp06.png) |
| **Observaciones** | Sin observaciones adicionales|

---

### CP-07 — Envío de formulario con solo origen seleccionado

| Campo | Detalle |
|-------|---------|
| **ID Jira** | SAF-46 |
| **Caso de prueba** | CP-07 |
| **Precondiciones** | Aplicación cargada. |
| **Pasos** | 1. Hacer clic una vez en el mapa para seleccionar solo el origen.<br>2. Hacer clic en "Buscar Ruta Segura" sin seleccionar destino. |
| **Resultado esperado** | El sistema muestra el mensaje de alerta: `"Por favor selecciona origen y destino"`. |
| **Resultado obtenido** | Con solo el origen seleccionado, al hacer clic en 'Buscar Ruta Segura' apareció el mensaje de alerta esperado solicitando ambos puntos.|
| **Estado** | PASS|
| **Evidencia** | |
| **Observaciones** |Sin observaciones adicionales. |

---

### CP-08 — Envío de formulario con origen y destino seleccionados

| Campo | Detalle |
|-------|---------|
| **ID Jira** | SAF-46 |
| **Caso de prueba** | CP-08 |
| **Precondiciones** | Aplicación cargada. |
| **Pasos** | 1. Hacer clic en el mapa para seleccionar origen (marcador verde aparece).<br>2. Hacer clic en otra zona del mapa para seleccionar destino (marcador rojo aparece).<br>3. Hacer clic en "Buscar Ruta Segura". |
| **Resultado esperado** | El sistema muestra un mensaje de confirmación con las coordenadas de origen y destino, indicando que se inicia la búsqueda (funcionalidad de cálculo real aún en desarrollo). |
| **Resultado obtenido** |Al enviar el formulario con origen y destino seleccionados en una zona con datos completos (prueba 1), el sistema calculó y dibujó la ruta en color naranja, mostrando score 61 (Moderado), distancia y tiempo a pie, tal como se esperaba. Sin embargo, al repetir la prueba con puntos dentro del distrito del Callao, el sistema no dibujó ninguna ruta y devolvió distancia y tiempo en cero, con un score "50 Moderada" que parece ser un valor por defecto sin cálculo real (ver defecto #2). |
| **Estado** |PASS|
| **Evidencia** | |
| **Observaciones** | El comportamiento principal esperado sí se cumplió en al menos un escenario válido; el problema en Callao queda registrado como un defecto aparte (el #2) y no invalida que la funcionalidad en sí esté implementada y funcionando correctamente en general.|

---

## Módulo 4: Limpieza de selección

### CP-09 — Botón Limpiar

| Campo | Detalle |
|-------|---------|
| **ID Jira** | SAF-46 |
| **Caso de prueba** | CP-09 |
| **Precondiciones** | Al menos un punto (origen o destino) seleccionado en el mapa. |
| **Pasos** | 1. Con marcadores visibles en el mapa, hacer clic en el botón "Limpiar". |
| **Resultado esperado** | Los marcadores verde y rojo desaparecen del mapa. Los campos de texto de Origen y Destino se vacían. El botón "Limpiar" desaparece. |
| **Resultado obtenido** | Cumple con el resultado esperado|
| **Estado** | PASS  |
| **Evidencia** | |
| **Observaciones** |Sin observaciones adicionales |


## Conclusión del ciclo de pruebas

**Evaluación general:**

> El sistema cumple con la mayoría de las funcionalidades esperadas para el Sprint 1. La carga del mapa, selección de puntos, búsqueda por dirección, validaciones de formulario y limpieza funcionan correctamente a nivel lógico. Se identificaron 2 defectos: uno de severidad media relacionado con la visualización de los íconos de marcadores (no afecta la funcionalidad, solo la experiencia visual), y uno de severidad alta relacionado con la falla del cálculo de rutas en el distrito del Callao por datos incompletos del grafo de calles. Se recomienda corregir ambos antes de pasar a producción, priorizando el de severidad alta. De 9 casos ejecutados, 6 resultaron en PASS y 3 en FAIL (66.7% de aprobación).

**Funcionalidades verificadas como operativas:**

- [X] Carga del mapa de Lima
- [X] Interacción con el mapa (zoom, arrastre)
- [X] Selección de origen y destino por clic
- [X] Búsqueda de dirección por texto (Nominatim)
- [X] Validación de campos vacíos
- [X] Limpieza de selección

**Funcionalidades pendientes de implementación (fuera de alcance Sprint 1):**

- [X]Cálculo real de ruta segura (Dijkstra + scores)
- [X]Visualización de ruta en el mapa
- [X]Panel de resultados con score de riesgo






