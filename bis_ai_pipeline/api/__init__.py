"""
bis_ai_pipeline/api/__init__.py
Package init — re-exports the FastAPI app factory for the entry point.
"""

from bis_ai_pipeline.api.main import create_app

__all__ = ["create_app"]
