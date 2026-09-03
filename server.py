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
    import server
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    server.run_server(port=port)
