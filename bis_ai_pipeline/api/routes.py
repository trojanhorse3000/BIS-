"""
bis_ai_pipeline/api/routes.py
All REST endpoints for the BIS AI Pipeline.

Endpoints
─────────
GET  /health                         — liveness probe for the MERN app
POST /api/query                      — main inference endpoint
GET  /api/history                    — recent queries (for UI timeline)
GET  /api/stats                      — dashboard statistics
GET  /api/standards                  — browse standards (paginated)
GET  /api/standards/search           — search standards by keyword / IS number
GET  /api/crosswalk                  — browse crosswalk (paginated)
GET  /api/crosswalk/search           — search crosswalk by product / HS code
GET  /api/huid/standards             — hallmarking standard reference
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from bis_ai_pipeline.api.models import (
    ErrorResponse,
    HealthResponse,
    HistoryEntry,
    HistoryResponse,
    QueryRequest,
    QueryResponse,
    StatsData,
    StatsResponse,
)
from bis_ai_pipeline.api.storage import QueryHistory
from bis_ai_pipeline.pipeline.generate import AnswerGenerator
from bis_ai_pipeline.pipeline.intent import classify_intent
from bis_ai_pipeline.pipeline.normalize import extract_entities, normalize_query
from bis_ai_pipeline.pipeline.retrieve import HybridRetriever

router = APIRouter()

# ── Lazy singleton initialisation ────────────────────────────────────────────

_retriever: Optional[HybridRetriever] = None
_generator: Optional[AnswerGenerator] = None
_history: Optional[QueryHistory] = None


def _get_retriever() -> HybridRetriever:
    global _retriever
    if _retriever is None:
        _retriever = HybridRetriever()
    return _retriever


def _get_generator() -> AnswerGenerator:
    global _generator
    if _generator is None:
        _generator = AnswerGenerator()
    return _generator


def _get_history() -> QueryHistory:
    global _history
    if _history is None:
        _history = QueryHistory()
    return _history


# ════════════════════════════════════════════════════════════════════════════
# Health & Info
# ════════════════════════════════════════════════════════════════════════════

@router.get("/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    return HealthResponse(
        message="BIS AI Pipeline API is healthy",
        version="2.0.0",
        components={
            "sqlite_db": "bis_data.db",
            "chroma_store": "chroma_store/",
            "pipeline": "normalise → intent → hybrid-retrieve → generate",
        },
    )


# ════════════════════════════════════════════════════════════════════════════
# Main Query Endpoint
# ════════════════════════════════════════════════════════════════════════════

@router.post("/api/query", response_model=QueryResponse, tags=["query"])
def run_query(payload: QueryRequest) -> QueryResponse:
    t0 = time.perf_counter()

    # 1 — Normalise & extract entities
    cleaned = normalize_query(payload.query)
    entities = extract_entities(payload.query)

    # 2 — Classify intent
    intent_data = classify_intent(cleaned, entities)
    intent_value = intent_data["intent"].value if hasattr(intent_data["intent"], "value") else str(intent_data["intent"])

    # 3 — Hybrid retrieval
    retriever = _get_retriever()
    retrieved = retriever.retrieve(cleaned, intent_data, entities)

    # 4 — Answer generation
    generator = _get_generator()
    is_hindi = entities.get("is_hindi", False)
    response = generator.generate(cleaned, intent_data, retrieved, is_hindi=is_hindi)

    latency_ms = round((time.perf_counter() - t0) * 1000, 2)

    # Persist to history
    history = _get_history()
    history.add(
        query=payload.query,
        intent=intent_value,
        source=response.get("source", "UNKNOWN"),
        verified=response.get("verified", False),
        is_refusal=response.get("is_refusal", False),
        latency_ms=latency_ms,
        entities=entities,
    )

    return QueryResponse(
        query=payload.query,
        cleaned_query=cleaned,
        entities=entities,
        intent={
            "intent": intent_value,
            "confidence": intent_data.get("confidence", 1.0),
            "primary_target": intent_data.get("primary_target"),
            "reason": intent_data.get("reason"),
        },
        retrieved=retrieved,
        answer=response["answer"],
        citations=response.get("citations", []),
        source=response.get("source", "UNKNOWN"),
        verified=response.get("verified", False),
        is_refusal=response.get("is_refusal", False),
        latency_ms=latency_ms,
    )


# ════════════════════════════════════════════════════════════════════════════
# Query History
# ════════════════════════════════════════════════════════════════════════════

@router.get("/api/history", response_model=HistoryResponse, tags=["history"])
def get_history(
    limit: int = Query(50, ge=1, le=200, description="Max rows to return"),
    intent: Optional[str] = Query(None, description="Filter by intent type"),
):
    history = _get_history()
    entries = history.get_recent(limit)

    if intent:
        entries = [e for e in entries if e.get("intent") == intent.upper()]

    return HistoryResponse(
        total=len(entries),
        entries=[HistoryEntry(**e) for e in entries],
    )


# ════════════════════════════════════════════════════════════════════════════
# Dashboard Stats
# ════════════════════════════════════════════════════════════════════════════

@router.get("/api/stats", response_model=StatsResponse, tags=["analytics"])
def get_stats():
    history = _get_history()
    stats = history.get_stats()
    return StatsResponse(data=StatsData(**stats))


# ════════════════════════════════════════════════════════════════════════════
# Standards Browser
# ════════════════════════════════════════════════════════════════════════════

@router.get("/api/standards", tags=["standards"])
def list_standards(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="Filter by status, e.g. ACTIVE"),
):
    import sqlite3, os
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bis_data.db")
    if not os.path.exists(db_path):
        raise HTTPException(status_code=503, detail="Database not initialised — run init_db.py")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        where = "WHERE 1=1"
        params: list = []
        if status:
            where += " AND status = ?"
            params.append(status.upper())

        cur.execute(f"SELECT COUNT(*) FROM standards {where}", params)
        total = cur.fetchone()[0]

        cur.execute(
            f"SELECT * FROM standards {where} ORDER BY is_number LIMIT ? OFFSET ?",
            [*params, page_size, (page - 1) * page_size],
        )
        rows = [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

    return {"status": "ok", "data": {"items": rows, "total": total, "page": page, "page_size": page_size}}


@router.get("/api/standards/search", tags=["standards"])
def search_standards(
    q: str = Query(..., min_length=1, description="Search keyword or IS number"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    import sqlite3, os
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bis_data.db")
    if not os.path.exists(db_path):
        raise HTTPException(status_code=503, detail="Database not initialised")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        like = f"%{q}%"
        cur.execute(
            """
            SELECT * FROM standards
            WHERE is_number LIKE ? OR title LIKE ? OR technical_committee LIKE ?
            ORDER BY is_number
            LIMIT ? OFFSET ?
            """,
            (like, like, like, page_size, (page - 1) * page_size),
        )
        rows = [dict(r) for r in cur.fetchall()]

        cur.execute(
            """
            SELECT COUNT(*) FROM standards
            WHERE is_number LIKE ? OR title LIKE ? OR technical_committee LIKE ?
            """,
            (like, like, like),
        )
        total = cur.fetchone()[0]
    finally:
        conn.close()

    return {"status": "ok", "data": {"items": rows, "total": total, "page": page, "page_size": page_size}}


# ════════════════════════════════════════════════════════════════════════════
# Crosswalk Browser
# ════════════════════════════════════════════════════════════════════════════

@router.get("/api/crosswalk", tags=["crosswalk"])
def list_crosswalk(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    scheme: Optional[str] = Query(None, description="Filter by scheme, e.g. 'Scheme I (ISI Mark)'"),
):
    import sqlite3, os
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bis_data.db")
    if not os.path.exists(db_path):
        raise HTTPException(status_code=503, detail="Database not initialised")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        params: list = []
        where = "WHERE 1=1"
        if scheme:
            where += " AND scheme LIKE ?"
            params.append(f"%{scheme}%")

        cur.execute(f"SELECT COUNT(*) FROM crosswalk {where}", params)
        total = cur.fetchone()[0]

        cur.execute(
            f"SELECT * FROM crosswalk {where} ORDER BY is_number LIMIT ? OFFSET ?",
            [*params, page_size, (page - 1) * page_size],
        )
        rows = [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

    return {"status": "ok", "data": {"items": rows, "total": total, "page": page, "page_size": page_size}}


@router.get("/api/crosswalk/search", tags=["crosswalk"])
def search_crosswalk(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    import sqlite3, os
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bis_data.db")
    if not os.path.exists(db_path):
        raise HTTPException(status_code=503, detail="Database not initialised")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        like = f"%{q}%"
        cur.execute(
            """
            SELECT * FROM crosswalk
            WHERE product LIKE ? OR product_category LIKE ? OR is_number LIKE ? OR qco_number LIKE ?
            ORDER BY is_number
            LIMIT ? OFFSET ?
            """,
            (like, like, like, like, page_size, (page - 1) * page_size),
        )
        rows = [dict(r) for r in cur.fetchall()]

        cur.execute(
            """
            SELECT COUNT(*) FROM crosswalk
            WHERE product LIKE ? OR product_category LIKE ? OR is_number LIKE ? OR qco_number LIKE ?
            """,
            (like, like, like, like),
        )
        total = cur.fetchone()[0]
    finally:
        conn.close()

    return {"status": "ok", "data": {"items": rows, "total": total, "page": page, "page_size": page_size}}


# ════════════════════════════════════════════════════════════════════════════
# HUID Reference
# ════════════════════════════════════════════════════════════════════════════

@router.get("/api/huid/standards", tags=["huid"])
def get_huid_standards():
    import sqlite3, os
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bis_data.db")
    if not os.path.exists(db_path):
        raise HTTPException(status_code=503, detail="Database not initialised")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM huid_reference ORDER BY CAST(gold_fineness_grade AS REAL) DESC")
        rows = [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

    return {"status": "ok", "data": rows}
