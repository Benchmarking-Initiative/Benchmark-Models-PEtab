"""
Benchmark Models PEtab.

Python tool to access the model collection.
"""

from .base import get_problem, get_problem_yaml_path
from .C import MODEL_DIRS, MODELS, MODELS_DIR
from .version import __version__
from .overview import get_overview_df
