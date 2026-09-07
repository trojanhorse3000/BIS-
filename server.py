"""
Root wrapper for server.py
Allows launching the web server directly from workspace root:
    python server.py
"""
import os
import sys

TARGET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bis_ai_pipeline")
sys.path.insert(0, TARGET_DIR)

if __name__ == "__main__":
    from bis_ai_pipeline.server import app
    import uvicorn
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    print(f"\n{'='*60}")
    print(f" BIS AI Pipeline — FastAPI Server")
    print(f" Docs:    http://localhost:{port}/docs")
    print(f" Health:  http://localhost:{port}/health")
    print(f" Port:    {port}")
    print(f"{'='*60}\n")
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)
