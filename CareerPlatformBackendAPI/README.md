# CareerPlatformBackendAPI

This backend now uses SQLite by default for local development and test environments through SQLAlchemy. No external PostgreSQL service is required to start the API or run basic CRUD operations.

## Quick start

1. Optionally create a `.env` based on `.env.example` (not required for SQLite defaults).
2. Install dependencies:
   - pip install -r requirements.txt
3. Run the server:
   - uvicorn src.api.main:app --host 0.0.0.0 --port 3001 --reload

On first start, a local SQLite database file (`career_platform.db`) will be created in the working directory and all tables will be initialized automatically.

If you want a few sample roles auto-created for testing, set `SEED_SAMPLE_DATA=1` in your environment (or `.env`) before starting the server.

## Configuration

- DB_URL (optional): complete SQLAlchemy URL. Defaults to `sqlite:///./career_platform.db`.
- SQLITE_PATH (optional): path to the SQLite file; used only if DB_URL is not set.
- SEED_SAMPLE_DATA (optional): when truthy (e.g., `1`, `true`, `yes`), seeds a few sample roles on startup if the roles table is empty.

Examples:
- SQLite (default): `DB_URL=sqlite:///./career_platform.db`
- Custom path via SQLITE_PATH: `SQLITE_PATH=/data/career_platform.db`
- Enable seeding: `SEED_SAMPLE_DATA=1`
- PostgreSQL (optional, not required for dev): `DB_URL=postgresql+psycopg2://USER:PASSWORD@HOST:5432/DBNAME`  
  Note: running with PostgreSQL would require installing a driver such as `psycopg2-binary`. This project does not depend on it by default.

## Roles API (SQLite-backed)

The API exposes a `roles` resource with versioned endpoints (`/api/v1`) to validate persistence using SQLite:

- GET /api/v1/roles — list all roles
- POST /api/v1/roles — create a role
- GET /api/v1/roles/{id} — get a role by ID

Optionally set `SEED_SAMPLE_DATA=1` to seed a few roles (e.g., Chief Architect, CTO, VP Engineering, Enterprise Architect) on startup if the table is empty.

## Sample CRUD (Templates)

The API also exposes a simple `templates` resource to validate persistence using SQLite:

- POST /templates
- GET /templates
- GET /templates/{template_id}
- PUT /templates/{template_id}
- DELETE /templates/{template_id}

These endpoints use SQLAlchemy and persist data into the SQLite database file.

## OpenAPI

When the server is running, visit `/docs` for the interactive Swagger UI.  
To regenerate the static `interfaces/openapi.json`, run:

```bash
python -m src.api.generate_openapi
```
