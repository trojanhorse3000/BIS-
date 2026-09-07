"""
bis_ai_pipeline/api/models.py
Pydantic request/response schemas for the MERN-ready REST API.
All response payloads follow a consistent envelope:
    { "status": "ok"|"error", "data": ..., "message": "..." }
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Request schemas ────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    """Incoming chat / query payload from the MERN frontend."""

    query: str = Field(..., min_length=1, max_length=1000, description="User query string")
    lang: Optional[str] = Field("en", pattern="^(en|hi)$", description="Output language: 'en' or 'hi'")
    include_telemetry: bool = Field(True, description="Whether to return pipeline internals for the inspector panel")


# ── Response schemas ───────────────────────────────────────────────────────────

class EntityData(BaseModel):
    is_numbers: List[str] = []
    huid_codes: List[str] = []
    hs_codes: List[str] = []
    product_terms: List[str] = []
    search_keywords: List[str] = []
    detected_input_lang: str = "en"
    requested_output_lang: str = "en"
    is_hindi: bool = False


class IntentData(BaseModel):
    intent: str
    confidence: float
    primary_target: Optional[str] = None
    reason: Optional[str] = None


class VectorResult(BaseModel):
    id: str
    text: str
    metadata: Dict[str, Any]
    similarity_score: float


class StructuredResult(BaseModel):
    """Wrap arbitrary SQLite row dicts for consistent typing."""

    model_config = {"arbitrary_types_allowed": True}
    raw: Dict[str, Any]


class RetrievedData(BaseModel):
    structured_results: List[Dict[str, Any]] = []
    vector_results: List[VectorResult] = []
    additional_count: int = 0
    context_type: str = "GENERAL_KNOWLEDGE"


class Citation(BaseModel):
    is_number: str
    product: str
    title: str
    scheme: str
    source_url: str
    score: float


class QueryResponse(BaseModel):
    """Envelope for a single pipeline inference."""

    status: str = "ok"
    query: str
    cleaned_query: str
    entities: EntityData
    intent: IntentData
    retrieved: RetrievedData
    answer: str
    citations: List[Citation]
    source: str          # e.g. "SQLITE_HUID_TABLE", "CHROMADB_VECTOR_STORE", "DOMAIN_REFUSAL_POLICY"
    verified: bool
    is_refusal: bool
    latency_ms: float


class HistoryEntry(BaseModel):
    """A persisted query-history row."""

    id: Optional[int] = None   # None for in-memory rows not yet flushed
    query: str
    intent: str
    source: str
    verified: bool
    is_refusal: bool
    latency_ms: float
    timestamp: str       # ISO-8601


class HistoryResponse(BaseModel):
    status: str = "ok"
    total: int = 0
    entries: List[HistoryEntry] = []


class StatsData(BaseModel):
    total_queries: int = 0
    total_huid_queries: int = 0
    total_standard_queries: int = 0
    total_refusals: int = 0
    avg_latency_ms: float = 0.0
    latest_query_at: Optional[str] = None


class StatsResponse(BaseModel):
    status: str = "ok"
    data: StatsData


class HealthResponse(BaseModel):
    status: str = "ok"
    message: str = "BIS AI Pipeline API is healthy"
    version: str = "2.0.0"
    components: Dict[str, str] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    status: str = "error"
    code: int
    message: str
    detail: Optional[str] = None


# ── Convenience helpers ────────────────────────────────────────────────────────

def ok_response(data: Any, message: str = "Success") -> Dict[str, Any]:
    return {"status": "ok", "data": data, "message": message}


def error_response(code: int, message: str, detail: Optional[str] = None) -> Dict[str, Any]:
    return {"status": "error", "code": code, "message": message, "detail": detail}
