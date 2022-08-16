"""Constants."""

import os
from typing import List

BASE_DIR: str = os.path.abspath(os.path.dirname(__file__))
MODELS_DIR: str = os.path.join(BASE_DIR, "Benchmark-Models")

MODELS: List[str] = os.listdir(MODELS_DIR)
MODEL_DIRS: List[str] = [os.path.join(MODELS_DIR, d) for d in MODELS]
