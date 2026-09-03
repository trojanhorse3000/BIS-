"""
Root wrapper for test_pipeline.py
Allows running `python test_pipeline.py` directly from the workspace root.
"""
import os
import sys

TARGET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bis_ai_pipeline")
sys.path.insert(0, TARGET_DIR)

if __name__ == "__main__":
    import test_pipeline
    test_pipeline.run_all_tests()
