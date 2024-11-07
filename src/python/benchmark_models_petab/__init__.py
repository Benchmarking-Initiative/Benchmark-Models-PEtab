"""
Benchmark Models PEtab.

Python tool to access the model collection.
"""

from .base import get_problem, get_problem_yaml_path
from .C import MODEL_DIRS, MODELS, MODELS_DIR
from .overview import get_overview_df
from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("benchmark_models_petab")
except PackageNotFoundError:
    # package is not installed
    pass
