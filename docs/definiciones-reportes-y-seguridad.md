# Definiciones del módulo de reportes y política de seguridad

Documento de definiciones que sustenta el módulo de reportes ciudadanos y las reglas de seguridad del sistema.

## 1. Política de seguridad

### Niveles de acceso

| Nivel | Operaciones |
| --- | --- |
| **Público** (sin autenticación) | Consultar ruta (`/route`), geocodificar (`/geocode`), registro e inicio de sesión (`/auth`), listar reportes del mapa (`GET /reports`) y **reporte rápido modo 1** (con rate limiting por IP) |
| **Con sesión** (token JWT) | Reportes modo 2 y 3, adjuntar documentos y gestión de los reportes propios |
| **Rol moderador** | Cola de moderación, revisión de documentos y aprobación/rechazo (`/moderation/*`) |

### Datos protegidos

- **Contraseñas:** se almacenan únicamente como hash; nunca en texto plano.
- **Documentos sustentatorios:** acceso restringido al rol moderador; no se exponen públicamente.
- **Identidad del autor:** el listado público de reportes no expone datos personales.
- **Endpoints anónimos:** protegidos con rate limiting para mitigar abuso.

## 2. Taxonomía de incidencias y campos por modo

Tipos de incidencia válidos: `robo`, `asalto`, `violencia`, `acoso`, `droga`, `vandalismo`, `ocupacion_via`, `venta_ambulante`, `otro`.

| Campo | Modo 1 | Modo 2 | Modo 3 |
| --- | :---: | :---: | :---: |
| Tipo de incidencia | Requerido | Requerido | Requerido |
| Ubicación (punto en el mapa) | Requerido | Requerido | Requerido |
| Descripción | Opcional | Opcional | Opcional |
| Fecha del hecho | — | Requerido | Requerido |
| Documento sustentatorio | — | — | Requerido (≥ 1) |

**Reglas de visibilidad y expiración:**
- Los reportes de modo 1 y 2 se muestran como *no verificados*: son informativos y no afectan el cálculo del score.
- Un reporte de modo 3 solo pasa a *verificado* cuando un moderador aprueba sus documentos; recién entonces influye en el score.
- Los reportes con más de 365 días dejan de aportar al cálculo del score.

## 3. Criterios de validación de documentos y privacidad (Ley N.° 29733)

**Requisitos del archivo:**
- Formatos aceptados: PDF, JPG/JPEG, PNG.
- Tamaño máximo: 10 MB por archivo (50 MB por reporte).
- Se calcula un hash SHA-256 por archivo para garantizar integridad y evitar duplicados.

**Criterios de validación del moderador:**
- El documento es legible y corresponde a una denuncia u otro documento oficial.
- Guarda coherencia con el tipo, la ubicación y la fecha del reporte.
- El moderador aprueba (pasa a *verificado*) o rechaza indicando el motivo.

**Privacidad de datos personales (Ley N.° 29733):**
- **Finalidad:** los datos se usan solo para el cálculo de rutas y la moderación.
- **Minimización:** no se publican la identidad del autor ni los documentos.
- **Acceso restringido:** únicamente los moderadores acceden a los documentos.
- **Derechos del titular:** el usuario puede solicitar la supresión de su reporte o cuenta.

## 4. Peso y decaimiento de los reportes validados en el score

El score compuesto de cada segmento combina tres capas:

```
base      = 0.70 · district_score + 0.30 · context_score
compuesto = 0.85 · base + 0.15 · report_score
```

La capa de reportes verificados aporta el **15 %** del score final. El `report_score` de un segmento se calcula así:

- Solo intervienen reportes en estado *validado* ubicados dentro de un radio de **150 m** del segmento (consulta `ST_DWithin`).
- Cada reporte aporta: `peso_por_tipo × factor_de_severidad × decaimiento_temporal`.
  - **Peso por tipo:** robo y asalto 1.0; violencia 0.9; acoso 0.8; droga 0.7; vandalismo 0.5; ocupación de vía y venta ambulante 0.3; otro 0.4.
  - **Factor de severidad:** bajo 0.5; medio 0.75; alto 1.0; crítico 1.25.
  - **Decaimiento temporal:** el aporte se multiplica por `0.5^(edad_en_días / 90)`, es decir, se reduce a la mitad cada 90 días.
- **Corte:** los reportes con más de 365 días no aportan.
- **Saturación:** alrededor de 3 reportes recientes de peso máximo llevan el `report_score` a su valor máximo (1.0).
