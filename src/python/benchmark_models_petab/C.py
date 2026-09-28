"""Constants."""

import os
from typing import List

BASE_DIR: str = os.path.abspath(os.path.dirname(__file__))
PROBLEMS_DIRNAME: str = "problems"
MODELS_DIR: str = os.path.join(BASE_DIR, PROBLEMS_DIRNAME)

MODELS: List[str] = sorted(os.listdir(MODELS_DIR))
MODEL_DIRS: List[str] = [os.path.join(MODELS_DIR, d) for d in MODELS]

# layout of a single problem directory (`<MODELS_DIR>/<ProblemID>/...`)
V1_DIRNAME: str = "v1"
PROBLEM_FILENAME: str = "problem.yaml"
SIMULATIONS_FILENAME: str = "simulations.tsv"

GITHUB_REPO: str = "Benchmarking-Initiative/Benchmark-Models-PEtab"
GITHUB_DEFAULT_BRANCH: str = "master"
