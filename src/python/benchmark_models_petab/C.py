"""Constants."""

import os
from typing import List

BASE_DIR: str = os.path.abspath(os.path.dirname(__file__))
PROBLEMS_DIRNAME: str = "problems"
MODELS_DIR: str = os.path.join(BASE_DIR, PROBLEMS_DIRNAME)

MODELS: List[str] = sorted(os.listdir(MODELS_DIR))
MODEL_DIRS: List[str] = [os.path.join(MODELS_DIR, d) for d in MODELS]

#: Former problem IDs, mapped to the current ones.
#:  Accepted by the accessor functions, but not part of `MODELS`.
RENAMED_MODELS: dict[str, str] = {
    "Giordano_Nature2020": "Giordano_NatMed2020",
    "Schwen_PONE2014": "Schwen_PLoSOne2015",
    "Weber_BMC2015": "Weber_BMCSystBiol2015",
}

# layout of a single problem directory (`<MODELS_DIR>/<ProblemID>/...`)
V1_DIRNAME: str = "v1"
V2_DIRNAME: str = "v2"
PROBLEM_FILENAME: str = "problem.yaml"
SIMULATIONS_FILENAME: str = "simulations.tsv"
METADATA_FILENAME: str = "metadata.yaml"

GITHUB_REPO: str = "Benchmarking-Initiative/Benchmark-Models-PEtab"
GITHUB_DEFAULT_BRANCH: str = "master"
