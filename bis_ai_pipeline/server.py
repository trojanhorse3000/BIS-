"""
server.py
BIS AI Pipeline — FastAPI production server.

Launch modes
────────────
    python server.py                     # run on port 8000 (uvicorn)
    python server.py 9000                # custom port
    BIS_API_KEY=secret123 python server.py  # require API key

Environment variables
─────────────────────
    BIS_API_KEY      Single API key (legacy, also accepted as BIS_API_KEYS)
    BIS_API_KEYS     Comma-separated list of valid keys (preferred)
    PORT             Override default port (default: 8000)
"""

import os
import sys

# Ensure bis_ai_pipeline is importable when run from the repo root
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from bis_ai_pipeline.api.main import create_app
from bis_ai_pipeline.api.storage import QueryHistory

app = create_app()


@app.on_event("shutdown")
def _flush_on_shutdown():
    """Persist any in-memory history rows before the process exits."""
    h = QueryHistory()
    h.flush()
    print("[server] Query history flushed to SQLite.")


def _resolve_port() -> int:
    return int(os.environ.get("PORT", sys.argv[1] if len(sys.argv) > 1 else 8000))


if __name__ == "__main__":
    import uvicorn
    port = _resolve_port()
    print(f"\n{'='*60}")
    print(f" BIS AI Pipeline — FastAPI Server")
    print(f" Docs:    http://localhost:{port}/docs")
    print(f" Health:  http://localhost:{port}/health")
    print(f" Port:    {port}")
    print(f"{'='*60}\n")
    uvicorn.run("bis_ai_pipeline.server:app", host="0.0.0.0", port=port, reload=False)
