"""
bis_ai_pipeline/api/main.py
FastAPI application factory.

Call `create_app()` to get a configured FastAPI instance ready to mount.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from bis_ai_pipeline.api.middleware import create_key_middleware
from bis_ai_pipeline.api.routes import router


def create_app() -> FastAPI:
    app = FastAPI(
        title="BIS AI Regulatory Pipeline",
        description=(
            "REST API for the Bureau of Indian Standards AI assistant. "
            "Supports Indian Standard lookups, QCO crosswalk queries, "
            "HUID hallmark verification, and multilingual (Hindi/English) responses."
        ),
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Allow the MERN frontend to call the API from any origin during development.
    # Pin these to your actual frontend URL in production.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API-key auth (skip /health, /docs, /openapi.json)
    create_key_middleware(app)

    # Mount the business-logic router under /api
    app.include_router(router, prefix="")

    return app
