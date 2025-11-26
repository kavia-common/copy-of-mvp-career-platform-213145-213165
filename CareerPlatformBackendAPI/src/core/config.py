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
- MAPPING_SERVICE_URL: Base URL for the Node RoleMappingService (default: http://localhost:4000)
- MAPPING_HTTP_TIMEOUT_SECONDS: HTTP timeout per attempt for the mapping client (default: 2)
- MAPPING_HTTP_RETRIES: Number of retry attempts for the mapping client (default: 2)

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

    # RoleMappingService integration
    mapping_service_url: str
    mapping_http_timeout_seconds: float
    mapping_http_retries: int

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
    # Default to HS256 explicitly; allow override via env
    algorithm = os.getenv("JWT_ALGORITHM", "HS256")
    # Explicitly parse known integers/floats
    try:
        expire = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    except Exception:
        expire = 60

    seed_from_json = str_to_bool(os.getenv("SEED_FROM_JSON", "0"))
    ingestion_dir = os.getenv("INGESTION_JSON_DIR", "data/imports")

    mapping_url = os.getenv("MAPPING_SERVICE_URL", "http://localhost:4000")
    try:
        mapping_timeout = float(os.getenv("MAPPING_HTTP_TIMEOUT_SECONDS", "2"))
    except Exception:
        mapping_timeout = 2.0
    try:
        mapping_retries = int(os.getenv("MAPPING_HTTP_RETRIES", "2"))
    except Exception:
        mapping_retries = 2

    return Settings(
        jwt_secret_key=secret,
        jwt_algorithm=algorithm,
        access_token_expire_minutes=expire,
        seed_from_json=seed_from_json,
        ingestion_json_dir=ingestion_dir,
        mapping_service_url=mapping_url,
        mapping_http_timeout_seconds=mapping_timeout,
        mapping_http_retries=mapping_retries,
    )
