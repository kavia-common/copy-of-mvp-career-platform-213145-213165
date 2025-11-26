"""Role Mapping Service client.

This module integrates with the Node-based RoleMappingService. It provides
simple wrapper functions to fetch competency maps by role and compute role
adjacency, with built-in timeouts/retries and graceful error handling.

Configuration (env):
- MAPPING_SERVICE_URL: Base URL of the Node service (default: http://localhost:4000)
- MAPPING_HTTP_TIMEOUT_SECONDS: Per-attempt timeout in seconds (default: 2)
- MAPPING_HTTP_RETRIES: Number of retry attempts on transient failures (default: 2)
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

import httpx

from src.core.config import get_settings


class MappingServiceError(Exception):
    """Base exception for mapping service errors."""


class MappingServiceUnavailable(MappingServiceError):
    """Raised when mapping service is unavailable (network/timeouts/retries exhausted)."""


def _get_base_url() -> str:
    settings = get_settings()
    base = settings.mapping_service_url.rstrip("/")
    return base


def _get_timeout() -> float:
    settings = get_settings()
    return float(settings.mapping_http_timeout_seconds)


def _get_retries() -> int:
    settings = get_settings()
    return int(settings.mapping_http_retries)


def _should_retry(status_code: int) -> bool:
    # Retry on typical transient errors
    return status_code in (429, 500, 502, 503, 504)


def _request_json(
    method: str, path: str, params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any] | List[Any] | None:
    """Perform an HTTP request with simple retry/backoff and return JSON.

    Raises MappingServiceUnavailable when network/timeouts persist.
    Returns None for 404s.
    """
    base = _get_base_url()
    url = f"{base}/{path.lstrip('/')}"
    timeout = _get_timeout()
    retries = _get_retries()

    attempt = 0
    last_exc: Optional[Exception] = None

    while attempt <= retries:
        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.request(method=method.upper(), url=url, params=params)
                if resp.status_code == 404:
                    return None
                if 200 <= resp.status_code < 300:
                    if resp.content:
                        return resp.json()
                    return {}
                if _should_retry(resp.status_code) and attempt < retries:
                    attempt += 1
                    time.sleep(min(0.25 * attempt, 1.0))
                    continue
                # Non-retryable HTTP error
                raise MappingServiceError(
                    f"Unexpected status {resp.status_code} from mapping service at {url}"
                )
        except (httpx.ConnectError, httpx.ReadTimeout, httpx.ConnectTimeout, httpx.RemoteProtocolError) as exc:
            last_exc = exc
            if attempt < retries:
                attempt += 1
                time.sleep(min(0.25 * attempt, 1.0))
                continue
            raise MappingServiceUnavailable(f"Mapping service unavailable: {exc}") from exc
        except httpx.RequestError as exc:
            # Other request-level errors (DNS, TLS, etc.)
            last_exc = exc
            if attempt < retries:
                attempt += 1
                time.sleep(min(0.25 * attempt, 1.0))
                continue
            raise MappingServiceUnavailable(f"Mapping service unavailable: {exc}") from exc

    # Should not reach here
    if last_exc is not None:
        raise MappingServiceUnavailable(f"Mapping service unavailable: {last_exc}")
    raise MappingServiceUnavailable("Mapping service unavailable (no response)")


# PUBLIC_INTERFACE
def get_competency_map_for_role(role_name: str) -> Optional[Dict[str, int]]:
    """Get the required competency map for a role from the Node service.

    Args:
        role_name: Human-readable role name (case-insensitive).

    Returns:
        A dict of { competencyName: required_level } if found, or None if the role does not exist.

    Raises:
        MappingServiceUnavailable: When the service cannot be reached after retries.
        MappingServiceError: For non-404 HTTP errors.
    """
    role = (role_name or "").strip()
    if not role:
        return None
    data = _request_json("GET", "/api/v1/competency-map", params={"role": role})
    if data is None:
        return None
    # Expecting shape: { role, competencies: [...], map: {...} }
    mapping = data.get("map") if isinstance(data, dict) else None
    return mapping if isinstance(mapping, dict) else None


# PUBLIC_INTERFACE
def get_adjacent_roles(role_name: str, limit: int = 10, min_score: float = 0.0) -> Optional[Dict[str, Any]]:
    """Fetch adjacent roles with similarity scores for the given role.

    Args:
        role_name: Source role name.
        limit: Maximum number of results.
        min_score: Minimum score threshold (0..1).

    Returns:
        Response dict as returned by the Node service:
        { "role": str, "total": int, "items": [ { "role": str, "score": float, ... }, ... ] }
        or None if the role was not found (404).

    Raises:
        MappingServiceUnavailable: When the service cannot be reached after retries.
        MappingServiceError: For non-404 HTTP errors.
    """
    params: Dict[str, Any] = {
        "role": (role_name or "").strip(),
        "limit": int(limit),
        "minScore": float(min_score),
    }
    data = _request_json("GET", "/api/v1/adjacent-roles", params=params)
    return None if data is None else data  # pass-through JSON


# PUBLIC_INTERFACE
def get_adjacency_details(current_role: str, target_role: str) -> Optional[Dict[str, Any]]:
    """Fetch detailed adjacency between two roles.

    Args:
        current_role: Current role name.
        target_role: Target role name.

    Returns:
        Detailed response from Node service or None if either role is not found.

    Raises:
        MappingServiceUnavailable: When the service cannot be reached after retries.
        MappingServiceError: For non-404 HTTP errors.
    """
    params: Dict[str, Any] = {
        "currentRole": (current_role or "").strip(),
        "targetRole": (target_role or "").strip(),
    }
    data = _request_json("GET", "/api/v1/mappings/adjacency", params=params)
    return None if data is None else data
