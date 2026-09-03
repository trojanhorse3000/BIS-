"""
Root wrapper for load_vectors.py
Allows running `python load_vectors.py` directly from the workspace root.
"""
import os
import sys

TARGET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bis_ai_pipeline")
sys.path.insert(0, TARGET_DIR)

if __name__ == "__main__":
    import load_vectors
    load_vectors.ingest_vectors()
