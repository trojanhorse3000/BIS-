"""
Root wrapper for init_db.py
Allows running `python init_db.py` directly from the workspace root.
"""
import os
import sys

TARGET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bis_ai_pipeline")
sys.path.insert(0, TARGET_DIR)

if __name__ == "__main__":
    import init_db
    init_db.initialize_database()
