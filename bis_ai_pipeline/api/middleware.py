"""
bis_ai_pipeline/api/middleware.py
API-Key authentication middleware for the FastAPI application.

Usage:
    pass the `api_keys: set[str]` to `create_key_middleware()` or set the
    `BIS_API_KEYS` env-var (comma-separated).  Omitting the header or
    supplying a wrong key returns HTTP 401 immediately — no pipeline cost.
"""

from __future__ import annotations

import os
from typing import Iterable, Optional

from fastapi import Request, Response
from fastapi.responses import JSONResponse


def _load_api_keys(raw: Optional[str]) -> set[str]:
    """Parse comma-separated keys from env var; fall back to a single default."""
    if raw and raw.strip():
        return {k.strip() for k in raw.split(",") if k.strip()}
    # Fallback: single key from BIS_API_KEY
    key = os.environ.get("BIS_API_KEY", "")
    return {key} if key else set()


def create_key_middleware(app, api_keys: Optional[Iterable[str]] = None, header: str = "X-API-Key"):
    """
    Register an on-app-dependents middleware that validates the API key.

    Endpoints that do NOT require auth:
        GET  /health
        GET  /docs
        GET  /openapi.json
    """
    keys: set[str] = set(api_keys) if api_keys is not None else _load_api_keys(os.environ.get("BIS_API_KEYS"))

    skip_paths = {"/health", "/docs", "/openapi.json", "/redoc"}

    @app.middleware("http")
    async def api_key_middleware(request: Request, call_next):
        # Public paths are always allowed
        if request.url.path in skip_paths:
            return await call_next(request)

        # Key may be supplied as header or query param
        provided = (
            request.headers.get(header)
            or request.query_params.get("api_key")
            or ""
        ).strip()

        if not keys:
            # No keys configured → allow (dev mode)
            return await call_next(request)

        if not provided or provided not in keys:
            return JSONResponse(
                status_code=401,
                content={
                    "status": "error",
                    "code": 401,
                    "message": "Unauthorized — invalid or missing API key",
                },
            )

        return await call_next(request)

    return app
