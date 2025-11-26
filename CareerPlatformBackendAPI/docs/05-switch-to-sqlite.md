# 05 - Switch to SQLite

This backend now defaults to **SQLite** using **SQLAlchemy**, enabling easy local development and tests without provisioning an external PostgreSQL service.

## Summary of changes

- Added SQLAlchemy and configured a default SQLite URL: `sqlite:///./career_platform.db`
- Centralized DB config in `src/db/database.py` with:
  - `engine`, `SessionLocal`, and `Base`
  - SQLite-friendly `connect_args={"check_same_thread": False}`
- Auto-creates tables at app startup (`on_startup` in `src/api/main.py`)
- Implemented a sample CRUD resource (`templates`) to validate persistence
- Removed any hard dependency on PostgreSQL drivers from `requirements.txt` (no `psycopg2` required)

## Configuration

- `DB_URL` (optional): full SQLAlchemy URL. If not set, defaults to local SQLite.
- `SQLITE_PATH` (optional): path to the SQLite file when `DB_URL` is not set.

Examples:
- Default: `DB_URL=sqlite:///./career_platform.db`
- Custom path: set `SQLITE_PATH=/data/career_platform.db`
- PostgreSQL (optional for advanced users): `DB_URL=postgresql+psycopg2://USER:PASSWORD@HOST:5432/DBNAME`  
  To use PostgreSQL locally, install `psycopg2-binary` separately and ensure the database is available. This project does not require it for development.

## Migrations

For the MVP/local development, tables are auto-created on startup (`Base.metadata.create_all`).  
If/when full migrations are required, introduce `alembic` and configure it to target SQLite and/or PostgreSQL as needed.

## Running the server

```bash
pip install -r requirements.txt
uvicorn src.api.main:app --host 0.0.0.0 --port 3001 --reload
```

The SQLite database file (`career_platform.db`) is created automatically in the working directory.

## Verifying CRUD

Use the following endpoints:

- POST /templates
- GET /templates
- GET /templates/{template_id}
- PUT /templates/{template_id}
- DELETE /templates/{template_id}

Visit `/docs` for interactive API docs.
