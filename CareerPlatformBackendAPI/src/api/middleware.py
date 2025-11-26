"""Custom FastAPI middlewares for the Career Platform Backend API."""

from __future__ import annotations

import logging
import time
import uuid
from typing import Callable, Awaitable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


# PUBLIC_INTERFACE
class RequestIdLoggingMiddleware(BaseHTTPMiddleware):
    """Attach a request-id to every request and log request/response with timing.

    Behavior:
        - Propagates X-Request-ID header if present, otherwise generates a new UUID4.
        - Stores the value on request.state.request_id.
        - Adds X-Request-ID header to every response.
        - Logs at INFO:
            [rid=<id>] <method> <path> -> <status_code> (<ms> ms)
    """

    def __init__(self, app) -> None:
        super().__init__(app)
        self._logger = logging.getLogger("career_platform.request")

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        rid = (
            request.headers.get("X-Request-ID")
            or request.headers.get("X-Request-Id")
            or request.headers.get("x-request-id")
            or str(uuid.uuid4())
        )
        request.state.request_id = rid  # attach to request state for downstream usage

        start = time.monotonic()
        # Pre-request log (at debug to avoid noisy logs in CI unless enabled)
        self._logger.debug("[rid=%s] %s %s - start", rid, request.method, request.url.path)

        try:
            response = await call_next(request)
        finally:
            duration_ms = int((time.monotonic() - start) * 1000)
            # Post-request log (status code may not be available if raised before response creation)
            try:
                status_code = response.status_code  # type: ignore[attr-defined]
            except Exception:
                status_code = 500
            self._logger.info(
                "[rid=%s] %s %s -> %s (%d ms)",
                rid,
                request.method,
                request.url.path,
                status_code,
                duration_ms,
            )

        # Always include/propagate the request id back to the client
        response.headers["X-Request-ID"] = rid
        return response
