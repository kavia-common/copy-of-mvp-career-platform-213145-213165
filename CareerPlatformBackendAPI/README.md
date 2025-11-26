# CareerPlatformBackendAPI

This backend uses SQLite by default for local development and test environments through SQLAlchemy. No external PostgreSQL service is required to start the API or run basic CRUD operations.

## Quick start

1. Optionally create a `.env` based on `.env.example` (recommended).
2. Install dependencies:
   - pip install -r requirements.txt
3. Run the server:
   - uvicorn src.api.main:app --host 0.0.0.0 --port 3001 --reload

On first start, a local SQLite database file (`career_platform.db`) will be created in the working directory and all tables will be initialized automatically.

If you want a few sample roles auto-created for testing, set `SEED_SAMPLE_DATA=1` in your environment (or `.env`) before starting the server.

If you want full role/competency/mapping data seeded from JSON, set `SEED_FROM_JSON=1` (see Seeding section below). Sample JSON files are provided in `data/imports/`.

## Configuration

- DB_URL (optional): complete SQLAlchemy URL. Defaults to `sqlite:///./career_platform.db`.
- SQLITE_PATH (optional): path to the SQLite file; used only if DB_URL is not set.
- JWT_SECRET_KEY (required for non-dev): secret key for signing JWTs (see `.env.example`).
- JWT_ALGORITHM (optional): default `HS256`.
- ACCESS_TOKEN_EXPIRE_MINUTES (optional): default `60`.
- SEED_FROM_JSON (optional): when truthy (e.g., `1`, `true`, `yes`), reads JSON from `INGESTION_JSON_DIR` and upserts roles/competencies/mappings.
- INGESTION_JSON_DIR (optional): directory for JSON ingestion files. Default: `data/imports`.
- SEED_SAMPLE_DATA (optional): when truthy, seeds a few sample roles on startup if the roles table is empty (fallback/demo).
- REACT_APP_BACKEND_URL (optional): used by the development plan export stub to compose URLs.
- MAPPING_SERVICE_URL (optional): Base URL for the Node RoleMappingService (default `http://localhost:4000`).
- MAPPING_HTTP_TIMEOUT_SECONDS (optional): Per-attempt HTTP timeout used by the mapping client (default `2`).
- MAPPING_HTTP_RETRIES (optional): Total retry attempts for the mapping client (default `2`).

Examples:
- SQLite (default): `DB_URL=sqlite:///./career_platform.db`
- Custom path via SQLITE_PATH: `SQLITE_PATH=/data/career_platform.db`
- Enable JSON seeding: `SEED_FROM_JSON=1` and `INGESTION_JSON_DIR=data/imports`
- Enable sample roles: `SEED_SAMPLE_DATA=1`
- PostgreSQL (optional, not required for dev): `DB_URL=postgresql+psycopg2://USER:PASSWORD@HOST:5432/DBNAME`  
  Note: running with PostgreSQL would require installing a driver such as `psycopg2-binary`. This project does not depend on it by default.
- RoleMappingService: `MAPPING_SERVICE_URL=http://localhost:4000` (make sure the Node service is running)

## Auth (JWT) endpoints

- POST /api/v1/auth/register — create account (email, password, full_name)
- POST /api/v1/auth/login — authenticate (email, password) and receive a JWT `access_token`
- POST /api/v1/auth/logout — stateless logout (requires Authorization)
- GET /api/v1/auth/profile — retrieve current user profile (requires Authorization)
- PUT /api/v1/auth/profile — update profile fields (requires Authorization)

Quick test (example using curl):
```bash
# Register
curl -s -X POST http://localhost:3001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"Passw0rd!","full_name":"Example User"}'

# Login
TOKEN=$(curl -s -X POST http://localhost:3001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"Passw0rd!"}' | jq -r .access_token)

# Profile
curl -s http://localhost:3001/api/v1/auth/profile -H "Authorization: Bearer $TOKEN"
```

## Domain routers

The following versioned routers are registered and documented in OpenAPI:

- Competencies
  - GET /api/v1/competencies (auth required)
  - GET /api/v1/competencies/by-role?role_id=... (auth required)
- Assessments
  - POST /api/v1/competency-assessment (auth required)
- Gap Analysis
  - POST /api/v1/gap-analysis (auth required) — now integrates with the Node RoleMappingService to fetch required competency maps by role name; falls back to local DB mapping if the Node service is unavailable.
- Development Plans
  - POST /api/v1/development-plan (auth required)
  - POST /api/v1/development-plan/export (auth required)
- Role Mapping (via Node service with fallback)
  - GET /api/v1/role-adjacency?role=Chief%20Architect&limit=10&min_score=0 — suggest adjacent roles (auth required)
  - GET /api/v1/role-adjacency/details?current_role=Chief%20Architect&target_role=CTO — detailed comparison (auth required)
- Admin
  - GET /api/v1/admin/templates (auth + admin required)
  - POST /api/v1/admin/templates (auth + admin required)
  - GET /api/v1/admin/audit-logs (auth + admin required)

Additional demo CRUD:
- Templates (unversioned demo)
  - POST /templates
  - GET /templates
  - GET /templates/{template_id}
  - PUT /templates/{template_id}
  - DELETE /templates/{template_id}

Roles (SQLite-backed):
- GET /api/v1/roles — list roles
- POST /api/v1/roles — create role
- GET /api/v1/roles/{id} — get by id

## Role Mapping Service integration (Node/Express)

This backend integrates with a lightweight Node service that reads JSON role and competency data to provide:
- Competency maps by role name
- Adjacent role suggestions with similarity scores
- Detailed adjacency between two roles

Config:
- `MAPPING_SERVICE_URL` (default `http://localhost:4000`)
- `MAPPING_HTTP_TIMEOUT_SECONDS` (default `2`)
- `MAPPING_HTTP_RETRIES` (default `2`)

Behavior:
- Gap analysis uses the Node service to fetch the target role's required competencies (by role name) and compares with user-provided current levels. If the Node service is unavailable, the backend falls back to local DB mappings.
- Role adjacency endpoints call the Node service. When the service is unavailable, the backend computes results locally from DB mappings using a weighted-Jaccard similarity as a graceful fallback.

Start the Node service (from the embedded folder):
```bash
cd role-mapping-service
npm install
npm start
# Service will run on http://localhost:4000 by default
```

## Seeding from JSON (data/imports)

Enable ingestion by setting:
```
SEED_FROM_JSON=1
INGESTION_JSON_DIR=data/imports
```
Then start the server. On startup, the app will:
1. Create all tables.
2. Load JSON from the directory:
   - `roles.json` (array of roles)
   - `competencies.json` (array of competencies)
   - `role_competencies.json` (array of role-competency required levels)
3. Upsert records and commit if any changes were applied.

Sample files are provided in `data/imports/` and are safe to modify. See `data/imports/README.md` for schema details.

To verify:
- GET /api/v1/roles (should list roles from JSON)
- GET /api/v1/competencies (requires Authorization; should list competencies)
- GET /api/v1/competencies/by-role?role_id=1 (requires Authorization; shows required levels for that role)

## OpenAPI

When the server is running, visit `/docs` for the interactive Swagger UI.  
To regenerate the static `interfaces/openapi.json`, run:

```bash
python -m src.api.generate_openapi
```

This re-exports the live OpenAPI schema from the running app (including the Auth, Competencies, Assessment, Gap Analysis, Development Plan, Admin, and Role Mapping routers).

## SQLite notes

- Default local DB path: `./career_platform.db`
- Tables are auto-created on startup (no migrations required for the MVP).
- To reset local data, stop the server and delete the SQLite file.
