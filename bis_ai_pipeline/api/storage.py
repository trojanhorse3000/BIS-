"""
bis_ai_pipeline/api/storage.py
In-memory + SQLite query-history store.

Design:
    - Fast reads/writes go through an in-memory list (O(1)).
    - On every N-th write (default 5) the in-memory list is flushed to
      SQLite so history survives a server restart.
    - The MERN frontend calls GET /history to render the recent-queries
      sidebar / timeline.
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
HISTORY_DB = os.path.join(PARENT_DIR, "query_history.db")
FLUSH_EVERY = 5  # persist to SQLite every N new entries


class QueryHistory:
    def __init__(self, db_path: str = HISTORY_DB, flush_every: int = FLUSH_EVERY):
        self._db_path = db_path
        self._flush_every = flush_every
        self._lock = threading.Lock()
        self._buffer: List[Dict] = []
        self._count_since_flush = 0
        self._init_db()

    # ── DB bootstrap ─────────────────────────────────────────────────────────

    def _init_db(self) -> None:
        conn = sqlite3.connect(self._db_path)
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS query_history (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    query       TEXT NOT NULL,
                    intent      TEXT,
                    source      TEXT,
                    verified    INTEGER,
                    is_refusal  INTEGER,
                    latency_ms  REAL,
                    timestamp   TEXT NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_qh_ts ON query_history(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_qh_intent ON query_history(intent)")
            conn.commit()
        finally:
            conn.close()

    # ── Public API ───────────────────────────────────────────────────────────

    def add(
        self,
        query: str,
        intent: str,
        source: str,
        verified: bool,
        is_refusal: bool,
        latency_ms: float,
        entities: Optional[Dict] = None,
    ) -> None:
        row = {
            "query": query,
            "intent": intent,
            "source": source,
            "verified": verified,
            "is_refusal": is_refusal,
            "latency_ms": latency_ms,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "entities": entities or {},
        }
        with self._lock:
            self._buffer.append(row)
            self._count_since_flush += 1
            if self._count_since_flush >= self._flush_every:
                self._flush_locked()

    def _flush_locked(self) -> None:
        """Must be called while self._lock is held."""
        if not self._buffer:
            return
        conn = sqlite3.connect(self._db_path)
        try:
            cur = conn.cursor()
            for row in self._buffer:
                cur.execute(
                    """
                    INSERT INTO query_history
                        (query, intent, source, verified, is_refusal, latency_ms, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row["query"],
                        row["intent"],
                        row["source"],
                        int(row["verified"]),
                        int(row["is_refusal"]),
                        row["latency_ms"],
                        row["timestamp"],
                    ),
                )
            conn.commit()
        finally:
            conn.close()
        flushed = len(self._buffer)
        self._buffer.clear()
        self._count_since_flush = 0
        print(f"[QueryHistory] Flushed {flushed} row(s) to {self._db_path}")

    def get_recent(self, limit: int = 50) -> List[Dict]:
        with self._lock:
            # In-memory rows are newest first (append order), reverse for chronological
            memory_rows = list(reversed(self._buffer))

        conn = sqlite3.connect(self._db_path)
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, query, intent, source, verified, is_refusal, latency_ms, timestamp
                FROM query_history
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (limit,),
            )
            db_rows = [
                {
                    "id": r[0],
                    "query": r[1],
                    "intent": r[2],
                    "source": r[3],
                    "verified": bool(r[4]),
                    "is_refusal": bool(r[5]),
                    "latency_ms": r[6],
                    "timestamp": r[7],
                }
                for r in cur.fetchall()
            ]
        finally:
            conn.close()

        # Merge: DB rows first (persisted), then in-memory rows that aren't yet in DB
        db_ids = {r["id"] for r in db_rows if r.get("id")}
        merged = db_rows
        for mr in memory_rows:
            if not any(e["query"] == mr["query"] and e["timestamp"] == mr["timestamp"] for e in merged):
                merged.append({
                    "id": None,
                    "query": mr["query"],
                    "intent": mr["intent"],
                    "source": mr["source"],
                    "verified": mr["verified"],
                    "is_refusal": mr["is_refusal"],
                    "latency_ms": mr["latency_ms"],
                    "timestamp": mr["timestamp"],
                })
        return merged[:limit]

    def get_stats(self) -> Dict:
        with self._lock:
            memory_rows = list(reversed(self._buffer))

        conn = sqlite3.connect(self._db_path)
        try:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM query_history")
            db_count = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM query_history WHERE is_refusal = 1")
            db_refusals = cur.fetchone()[0]

            cur.execute("SELECT AVG(latency_ms) FROM query_history")
            row = cur.fetchone()
            db_avg = row[0] if row and row[0] is not None else 0.0

            cur.execute("SELECT intent, COUNT(*) as cnt FROM query_history GROUP BY intent ORDER BY cnt DESC LIMIT 5")
            intent_dist = {r[0]: r[1] for r in cur.fetchall()}

            cur.execute("SELECT timestamp FROM query_history ORDER BY timestamp DESC LIMIT 1")
            latest = cur.fetchone()

            cur.execute("SELECT COUNT(*) FROM query_history WHERE intent = 'STANDARD_LOOKUP'")
            std_count = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM query_history WHERE intent = 'HUID_VERIFICATION'")
            huid_count = cur.fetchone()[0]
        finally:
            conn.close()

        # Merge in-memory rows for live accuracy
        all_rows = [
            {"intent": r["intent"], "is_refusal": r["is_refusal"], "latency_ms": r["latency_ms"]}
            for r in memory_rows
        ]
        all_rows += [
            {"intent": "UNKNOWN", "is_refusal": False, "latency_ms": 0.0}
            for _ in range(db_count)
        ]

        total = len(all_rows)
        refusals = sum(1 for r in all_rows if r["is_refusal"])
        avg_lat = (
            sum(r["latency_ms"] for r in all_rows) / total if total else 0.0
        )

        return {
            "total_queries": db_count + len(memory_rows),
            "total_huid_queries": huid_count + sum(1 for r in memory_rows if r["intent"] == "HUID_VERIFICATION"),
            "total_standard_queries": std_count + sum(1 for r in memory_rows if r["intent"] == "STANDARD_LOOKUP"),
            "total_refusals": db_refusals + refusals,
            "avg_latency_ms": round(avg_lat, 2),
            "latest_query_at": latest[0] if latest else None,
            "intent_distribution": intent_dist,
        }

    def flush(self) -> None:
        with self._lock:
            self._flush_locked()
