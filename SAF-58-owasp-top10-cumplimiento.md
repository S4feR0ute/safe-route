# SAF-58 — Revisión y Documentación de Cumplimiento OWASP Top 10

**Proyecto:** SafeRoute Lima
**Responsable QA:** Anngie Salazar Alvarez
**Versión del sistema revisada:** Sprint 4 (rama `develop`, julio 2026)
**Referencia:** OWASP Top 10 2021 (https://owasp.org/Top10/)

---

## ¿Qué es OWASP Top 10?

OWASP (Open Worldwide Application Security Project) es una organización internacional de seguridad web. El "Top 10" es su lista de las vulnerabilidades más críticas y frecuentes en aplicaciones web, actualizada periódicamente. Esta revisión evalúa si SafeRoute Lima cubre cada categoría.

**Leyenda:**
- ✅ **Cubierto** — existe una medida de seguridad implementada y efectiva.
- ⚠️ **Parcialmente cubierto** — existe algo, pero con limitaciones o brechas.
- ❌ **No cubierto** — no existe ninguna medida para esta categoría.

---

## Resumen ejecutivo

| # | Categoría OWASP | Estado | Prioridad |
|---|---|---|---|
| A01 | Control de acceso roto | ⚠️ Parcial | Alta |
| A02 | Fallas criptográficas | ✅ Cubierto | — |
| A03 | Inyección | ✅ Cubierto | — |
| A04 | Diseño inseguro | ⚠️ Parcial | Media |
| A05 | Configuración de seguridad incorrecta | ✅ Cubierto | — |
| A06 | Componentes vulnerables y desactualizados | ⚠️ Parcial | Media |
| A07 | Fallas de identificación y autenticación | ✅ Cubierto | — |
| A08 | Fallas de integridad de software y datos | ⚠️ Parcial | Media |
| A09 | Fallas en registro y monitoreo de seguridad | ⚠️ Parcial | Baja |
| A10 | Falsificación de solicitudes del lado del servidor (SSRF) | ⚠️ Parcial | Media |

---

## Detalle por categoría

### A01 — Control de acceso roto ⚠️ Parcial

**¿Qué significa?** Que usuarios no autorizados puedan acceder a funciones o datos que no les corresponden.

**Lo que tiene el sistema:**
- Autenticación JWT implementada en `app/core/security.py` con verificación de firma y expiración.
- El endpoint de moderación (`/api/v1/moderation/*`) requiere token de moderador.
- Rate limiting diferenciado por endpoint: 30 req/min para `/auth/*`, 10 req/min para `/reports`.

**Brechas identificadas:**
- El endpoint principal `/api/v1/route` es completamente público — cualquier usuario (incluso no registrado) puede calcular rutas sin límite efectivo. Aunque hay rate limiting general (120 req/min), bajo carga concurrente el sistema ya mostró no poder manejar 20 peticiones simultáneas (ver SAF-55).
- No se verifica que un usuario solo pueda ver/modificar sus propios reportes de incidentes.

**Archivos revisados:** `app/api/route_endpoint.py`, `app/api/moderation_endpoints.py`, `app/core/auth_helper.py`

---

### A02 — Fallas criptográficas ✅ Cubierto

**¿Qué significa?** Datos sensibles expuestos por uso de criptografía débil o inexistente.

**Lo que tiene el sistema:**
- Contraseñas hasheadas con **PBKDF2-SHA256** con 100,000 iteraciones y salt aleatorio (`secrets.token_hex(16)`), implementado en `app/core/security.py`. Este es un algoritmo robusto y recomendado.
- JWT firmados con clave secreta configurable (`JWT_SECRET_KEY`) usando el algoritmo definido en `app/core/config.py`.
- Header `Strict-Transport-Security` configurado en `SecurityHeadersMiddleware` para forzar HTTPS en producción.
- Contraseñas limitadas a 72 caracteres (límite de PBKDF2/bcrypt) para prevenir ataques de DoS por contraseñas largas.

**Archivos revisados:** `app/core/security.py`, `app/middleware/security_middleware.py`

---

### A03 — Inyección ✅ Cubierto

**¿Qué significa?** Que datos maliciosos enviados por el usuario se ejecuten como comandos en la base de datos (SQL injection) u otros intérpretes.

**Lo que tiene el sistema:**
- Todas las consultas a la base de datos usan **SQLAlchemy ORM** con queries parametrizadas, lo que previene SQL injection por diseño (`app/db/session.py`).
- `SQLInjectionValidator` en `app/core/validators.py` detecta patrones SQL peligrosos (`UNION SELECT`, `DROP TABLE`, comentarios SQL, etc.) en inputs de texto.
- `InputSanitizationMiddleware` en `app/middleware/security_middleware.py` detecta y loguea patrones sospechosos en query parameters (`<script>`, `javascript:`, `onerror=`, etc.).

**Observación:** El middleware de sanitización solo loguea los patrones sospechosos pero no los bloquea. Dependiendo del contexto, podría ser conveniente bloquear activamente en vez de solo registrar.

**Archivos revisados:** `app/db/session.py`, `app/core/validators.py`, `app/middleware/security_middleware.py`

---

### A04 — Diseño inseguro ⚠️ Parcial

**¿Qué significa?** Falta de controles de seguridad desde el diseño de la arquitectura.

**Lo que tiene el sistema:**
- Rate limiting implementado con límites diferenciados por tipo de endpoint.
- Validación de inputs (coordenadas, email, contraseñas) antes de procesar.
- Separación de roles: ciudadano anónimo, ciudadano registrado, moderador.

**Brechas identificadas:**
- La prueba de carga (SAF-55) demostró que el sistema no tiene resiliencia bajo carga — el grafo se reconstruye en cada petición agotando el pool de conexiones (defecto DEF-SAF-55-01). Esto es un problema de diseño que puede usarse para un ataque de Denegación de Servicio (DoS) incluso con pocos usuarios.
- No hay mecanismo de circuit breaker ni timeout configurable por endpoint.

**Archivos revisados:** `app/services/routing_service.py`, `app/middleware/security_middleware.py`

---

### A05 — Configuración de seguridad incorrecta ✅ Cubierto

**¿Qué significa?** Configuraciones por defecto inseguras, headers de seguridad faltantes, o información sensible expuesta.

**Lo que tiene el sistema:**
- `SecurityHeadersMiddleware` agrega automáticamente a todas las respuestas:
  - `X-Content-Type-Options: nosniff` (previene MIME sniffing)
  - `X-Frame-Options: DENY` (previene clickjacking)
  - `X-XSS-Protection: 1; mode=block` (protección XSS en browsers antiguos)
  - `Content-Security-Policy` configurado (restringe fuentes de scripts, estilos, imágenes)
  - `Strict-Transport-Security` (fuerza HTTPS)
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `Permissions-Policy` (deshabilita cámara, micrófono, geolocalización del browser)
- CORS configurado en `api_app.py`.

**Archivos revisados:** `app/middleware/security_middleware.py`, `api_app.py`

---

### A06 — Componentes vulnerables y desactualizados ⚠️ Parcial

**¿Qué significa?** Uso de librerías con vulnerabilidades conocidas o sin actualizar.

**Lo que tiene el sistema:**
- El proyecto usa `requirements.txt` con versiones de dependencias listadas.

**Brechas identificadas:**
- No se encontró evidencia de un proceso automatizado de escaneo de dependencias (como `pip audit`, Dependabot, o Snyk) en el repositorio.
- Algunas dependencias ya mostraron advertencias de deprecación durante los tests (SQLAlchemy, Pydantic v1 validators).

**Recomendación:** Ejecutar `pip audit` periódicamente o configurar Dependabot en GitHub para alertas automáticas de vulnerabilidades en dependencias.

---

### A07 — Fallas de identificación y autenticación ✅ Cubierto

**¿Qué significa?** Debilidades en el sistema de login, gestión de sesiones o tokens.

**Lo que tiene el sistema:**
- JWT con expiración configurable, firma verificada en cada petición.
- `PasswordValidator` exige mínimo 8 caracteres, al menos una mayúscula, una minúscula y un número.
- `EmailValidator` valida formato de email y previene SQL injection en el campo.
- Rate limiting en endpoints de autenticación: máximo 30 peticiones/minuto por IP para `/auth/*`.
- Contraseñas hasheadas con PBKDF2-SHA256 (no almacenadas en texto plano).
- Tokens JWT con expiración — las sesiones no son indefinidas.

**Archivos revisados:** `app/core/security.py`, `app/core/validators.py`, `app/middleware/security_middleware.py`

---

### A08 — Fallas de integridad de software y datos ⚠️ Parcial

**¿Qué significa?** Código o datos que pueden ser modificados sin verificación de integridad (actualizaciones automáticas sin firma, deserialización insegura, etc.).

**Lo que tiene el sistema:**
- JWT con firma digital — los tokens no pueden modificarse sin invalidarse.
- Validación de tipos de datos con Pydantic en todos los schemas de entrada.

**Brechas identificadas:**
- No se encontró evidencia de verificación de integridad en la pipeline de despliegue (CI/CD).
- Los archivos subidos por usuarios (reportes de incidentes con documentos) se validan por tipo y tamaño, pero no se verifica firma o hash del contenido.

---

### A09 — Fallas en registro y monitoreo de seguridad ⚠️ Parcial

**¿Qué significa?** Que eventos de seguridad importantes no se registren o no generen alertas.

**Lo que tiene el sistema:**
- Logging configurado con `logging` de Python en múltiples módulos.
- `InputSanitizationMiddleware` loguea patrones sospechosos detectados.
- `RateLimitMiddleware` loguea cuando una IP excede el límite.
- Los errores de cálculo de ruta se loguean con `logger.exception`.

**Brechas identificadas:**
- Los logs son solo locales (consola/archivo) — no hay integración con un sistema centralizado de monitoreo (como Sentry, Datadog, o ELK Stack).
- No hay alertas automáticas ante eventos críticos (múltiples intentos de login fallidos, errores 500 repetidos, etc.).
- No se encontró evidencia de retención de logs con política definida.

---

### A10 — Falsificación de solicitudes del lado del servidor (SSRF) ⚠️ Parcial

**¿Qué significa?** Que un atacante pueda hacer que el servidor realice peticiones HTTP a URLs arbitrarias, incluyendo recursos internos de la red.

**Lo que tiene el sistema:**
- El sistema hace peticiones externas a Nominatim (geocodificación) y a Overpass API (datos de OpenStreetMap), pero estas URLs están hardcodeadas en constantes (`app/core/constants.py`), no provienen de input del usuario.

**Brechas identificadas:**
- No se verifica que las URLs construidas para llamadas externas estén dentro de una lista blanca explícita.
- Si en el futuro se agrega funcionalidad donde el usuario pueda especificar URLs (por ejemplo, fuentes de datos externas), habría riesgo de SSRF sin controles adicionales.

**Riesgo actual:** Bajo, dado que las URLs externas son fijas y no controladas por el usuario.

---

## Hallazgos prioritarios

| Prioridad | Hallazgo | Categoría OWASP | Recomendación |
|---|---|---|---|
| 🔴 Alta | El sistema no resiste carga concurrente de 20 usuarios (DoS involuntario) | A04 | Implementar caché del grafo en memoria (ver SAF-55) |
| 🟡 Media | Sanitización detecta pero no bloquea inputs maliciosos | A03 | Evaluar si conviene bloquear activamente en `InputSanitizationMiddleware` |
| 🟡 Media | Sin escaneo automatizado de dependencias vulnerables | A06 | Configurar `pip audit` o Dependabot en GitHub |
| 🟡 Media | Sin sistema centralizado de monitoreo y alertas | A09 | Integrar Sentry u otro sistema de monitoreo de errores |
| 🟢 Baja | Riesgo potencial de SSRF si se agrega input de URLs por usuario | A10 | Documentar política de lista blanca para URLs externas |

---

## Conclusión

SafeRoute Lima implementa medidas de seguridad sólidas para un proyecto universitario en las áreas más críticas: criptografía de contraseñas (PBKDF2-SHA256), autenticación JWT, prevención de SQL injection via ORM, headers de seguridad completos, y rate limiting. Las brechas identificadas son principalmente en monitoreo, escaneo de dependencias, y resiliencia bajo carga — áreas que requieren madurez adicional para un despliegue en producción real.

El hallazgo más crítico sigue siendo el defecto DEF-SAF-55-01 (grafo reconstruido en cada petición), que expone el sistema a una Denegación de Servicio involuntaria bajo carga normal.

---

