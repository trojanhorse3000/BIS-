"""
Root wrapper for main.py
Allows running `python main.py` directly from the workspace root.
"""
import os
import sys

TARGET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bis_ai_pipeline")
sys.path.insert(0, TARGET_DIR)

if __name__ == "__main__":
    import main
    query = sys.argv[1] if len(sys.argv) > 1 else "Please verify gold hallmark HUID code AB1234"
    main.run_pipeline(query)
