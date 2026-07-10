# Manual Técnico y de Instalación — SafeRoute

Guía para levantar el sistema completo (base de datos, backend y frontend) en un entorno local.

## 1. Requisitos previos

| Herramienta | Versión recomendada | Nota |
| --- | --- | --- |
| Python | **3.12** | No usar 3.14: `osmnx`/`geopandas`/`shapely` no tienen wheels y fallan al compilar |
| Node.js | 18+ (probado con 22) | Para el frontend |
| PostgreSQL + PostGIS | 16 + 3.4 | Obligatorio PostGIS (geometrías) |
| Git | — | — |

## 2. Clonar el repositorio

```bash
git clone https://github.com/S4feR0ute/safe-route.git
cd safe-route
```

## 3. Base de datos (PostgreSQL + PostGIS)

**Opción A — Docker (más rápido):**
```bash
docker run -d --name saferoute-pg \
  -e POSTGRES_USER=saferoute -e POSTGRES_PASSWORD=saferoute -e POSTGRES_DB=saferoute \
  -p 5432:5432 postgis/postgis:16-3.4
```

**Opción B — Instalación nativa:** instalar PostgreSQL 16 y la extensión PostGIS, y crear la base `saferoute`.

**Aplicar el esquema** (13 tablas + índices):
```bash
psql "postgresql://saferoute:saferoute@localhost:5432/saferoute" -f backend/app/db/migrations/init_db.sql
# con Docker:
docker exec -i saferoute-pg psql -U saferoute -d saferoute < backend/app/db/migrations/init_db.sql
```

## 4. Backend (FastAPI)

```bash
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Crear un archivo `backend/.env`:
```env
DATABASE_URL_LOCAL=postgresql://saferoute:saferoute@localhost:5432/saferoute
JWT_SECRET_KEY=cambia_esto_por_un_secreto_largo
ENVIRONMENT=development
```

**Cargar los datos** (grafo OSM + criminalidad + contexto + scores). Es un proceso por lotes que puede tardar varios minutos:
```bash
python -m app.data_loader.orchestrator --list   # ver los pasos
python -m app.data_loader.orchestrator --all     # ejecutar todo en orden
```

**Levantar la API:**
```bash
uvicorn api_app:app --reload --port 8000
# verificar:
curl http://localhost:8000/api/v1/health   # -> {"status":"ok",...}
```

## 5. Frontend (React + Vite)

```bash
cd frontend
npm install
# Opcional: apuntar al backend (por defecto usa http://localhost:8000)
echo "VITE_API_URL=http://localhost:8000" > .env
npm run dev        # desarrollo -> http://localhost:5173
npm run build      # build de producción (dist/)
```

## 6. Variables de entorno

| Variable | Requerida | Default | Descripción |
| --- | --- | --- | --- |
| `DATABASE_URL_LOCAL` | **Sí** | — | Cadena de conexión PostgreSQL |
| `JWT_SECRET_KEY` | Recomendada | secreto de dev | Clave para firmar JWT (obligatoria fuera de desarrollo) |
| `JWT_EXPIRATION_MINUTES` | No | `30` | Expiración del token |
| `ENVIRONMENT` | No | `development` | `development` / `production` |
| `CORS_ORIGINS` | No | `*` | Orígenes permitidos (coma-separados) |
| `SIDPOL_SOURCE_URL` | No | Excel MININTER | Fuente de datos de criminalidad |
| `LOG_LEVEL` | No | `INFO` | Nivel de logging |
| `VITE_API_URL` (frontend) | No | `http://localhost:8000` | URL del backend |

## 7. Verificación y pruebas

```bash
# Backend (desde backend/, con el venv activo)
pytest
# Frontend E2E (Playwright)
cd frontend && npx playwright test
```

## 8. Notas

- **No hay `docker-compose` aún**: cada componente se levanta por separado siguiendo esta guía.
- La API de ruteo lee scores **pre-calculados**; si `/route` responde 503, falta ejecutar el Data Loader (paso 4).
- Endpoints principales: `/api/v1/route`, `/api/v1/geocode`, `/auth/*`, `/reports/*`, `/moderation/*`.
