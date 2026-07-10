# Manual de Usuario — SafeRoute

Guía de uso de la aplicación web dirigida al ciudadano. No requiere conocimientos técnicos.

## 1. Acceso

Abre la aplicación en el navegador (por defecto `http://localhost:5173`). Verás un **mapa de Lima** con:
- Arriba a la izquierda: el formulario **SafeRoute** (origen/destino).
- Arriba a la derecha: **Iniciar Sesión** / **Crear Cuenta** (o tu sesión si ya ingresaste).
- Abajo a la derecha: botón **Mostrar/Ocultar Alertas**.

El registro **no es obligatorio** para consultar rutas ni para reportar de forma rápida.

## 2. Consultar una ruta segura

1. Indica el **origen** y el **destino** de una de estas dos formas:
   - **Escribiendo la dirección** en los campos y eligiendo una sugerencia del autocompletado, o
   - **Haciendo click en el mapa**: el primer click marca el origen (📍) y el segundo el destino (📍).
2. Pulsa **"Buscar Ruta Segura"**.
3. El mapa dibujará la ruta y se centrará en ella.

Usa **"Limpiar"** para reiniciar los puntos.

## 3. Interpretar el resultado

- **Colores de la ruta** (según el riesgo de cada tramo):
  - 🟢 Verde = riesgo bajo
  - 🟡 Amarillo = riesgo medio
  - 🔴 Rojo = riesgo alto
- **Panel de resultado** (abajo a la izquierda): muestra el **score de seguridad** (0–100), la **categoría** (Segura / Moderada / Riesgosa), la **distancia** y el **tiempo de caminata** estimado.
- Haz click sobre un tramo de la ruta para ver su nombre y nivel de riesgo.

## 4. Ver alertas de la comunidad

En el mapa aparecen los reportes ciudadanos como marcadores:
- 🚨 = reporte **verificado** (con documento validado por un moderador).
- ⚠️ = reporte **pendiente / no verificado**.

Haz click en un marcador para ver el tipo de incidencia y su estado. Usa **"Mostrar/Ocultar Alertas"** para activar o desactivar estos marcadores. *No se muestran datos personales del autor.*

## 5. Reportar una incidencia

**Haz click derecho** sobre el punto del mapa donde ocurrió el hecho. Se abrirá la ventana **"Reportar Incidencia"**:

1. Elige el **Tipo de Incidente** (Robo a mano armada, Arrebato, Vandalismo, Agresión física, Zona oscura/Peligrosa).
2. Escribe una **Descripción** (opcional).
3. Pulsa **"Enviar Reporte"**.

Según tu situación, el reporte tendrá distinto alcance:

| Modo | Cómo | Efecto |
| --- | --- | --- |
| **Modo 1 — Anónimo** | Sin iniciar sesión | Se muestra en el mapa como no verificado. **No afecta** el cálculo de rutas. |
| **Modo 2 — Con cuenta** | Con sesión iniciada; se pide la **fecha exacta** del suceso | Queda asociado a tu identidad, pero sigue siendo informativo. |
| **Modo 3 — Con documento** | Con sesión + adjuntar la **denuncia policial** (PDF/JPG, máx. 10 MB) | Tras ser **validado por un moderador**, **sí influye** en el cálculo de rutas seguras. |

Todo reporte entra en estado *pendiente* hasta que un moderador lo revise.

## 6. Crear cuenta e iniciar sesión

- **Crear Cuenta**: click en "Crear Cuenta", ingresa correo y contraseña.
- **Iniciar Sesión**: click en "Iniciar Sesión" con tus credenciales.
- Con la sesión activa podrás reportar en **modo 2 y 3**. Usa **"Cerrar Sesión"** para salir.

## 7. Moderación de reportes (solo moderadores)

Los usuarios con rol **moderador** acceden a la página de moderación (`/moderador`):
1. Ver la **cola de reportes pendientes**.
2. Revisar el detalle de cada reporte.
3. **Aprobar** (pasa a *verificado* y afecta el score) o **Rechazar** (con motivo).

Solo los reportes **aprobados** modifican el cálculo de rutas.
