"""
Root wrapper for prompts.py
"""
import sys
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PIPELINE_DIR = os.path.join(CURRENT_DIR, "bis_ai_pipeline")
if PIPELINE_DIR not in sys.path:
    sys.path.insert(0, PIPELINE_DIR)

from pipeline.prompts import (
    CITATION_INSTRUCTION,
    FEW_SHOT_EXAMPLES,
    build_system_prompt,
    build_citation_prompt,
)
