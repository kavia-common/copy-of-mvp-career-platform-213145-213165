"""Core configuration for the Career Platform Backend API.

Handles environment variable configuration for JWT and application behavior.
Do not hardcode secrets in code; ensure environment variables are set in the runtime.

Environment variables (request these from the user or set in .env):
- JWT_SECRET_KEY: Secret key used to sign JWT tokens. REQUIRED for non-dev.
- JWT_ALGORITHM: JWT signing algorithm. Default: HS256
- ACCESS_TOKEN_EXPIRE_MINUTES: TOKEN expiration in minutes. Default: 60
- SEED_FROM_JSON: Set truthy to seed entities from JSON files at startup.
- INGESTION_JSON_DIR: Directory path with ingestion JSON files. Default: data/imports
- SEED_SAMPLE_DATA: Set truthy to seed sample Roles if roles table is empty (fallback demo).

Note: DB_URL/SQLITE_PATH are configured in src/db/database.py.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import timedelta


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables."""

    jwt_secret_key: str
    jwt_algorithm: str
    access_token_expire_minutes: int
    seed_from_json: bool
    ingestion_json_dir: str

    # PUBLIC_INTERFACE
    def access_token_expires(self) -> timedelta:
        """Compute the timedelta for access token expiry based on configuration."""
        return timedelta(minutes=self.access_token_expire_minutes)


def str_to_bool(value: str | None) -> bool:
    if not value:
        return False
    return value.strip().lower() in {"1", "true", "yes", "y"}


# PUBLIC_INTERFACE
def get_settings() -> Settings:
    """Create Settings object from environment variables."""
    secret = os.getenv("JWT_SECRET_KEY", "dev-secret-change-me")
    algorithm = os.getenv("JWT_ALGORITHM", "HS256")
    expire = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    seed_from_json = str_to_bool(os.getenv("SEED_FROM_JSON", "0"))
    ingestion_dir = os.getenv("INGESTION_JSON_DIR", "data/imports")
    return Settings(
        jwt_secret_key=secret,
        jwt_algorithm=algorithm,
        access_token_expire_minutes=expire,
        seed_from_json=seed_from_json,
        ingestion_json_dir=ingestion_dir,
    )
