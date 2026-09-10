"""Get a petab problem from the collection."""

from pathlib import Path

import petab.v1
import petab.v2
from petab.versions import get_major_version

from .C import MODELS_DIR

import pandas as pd

Problem = petab.v1.Problem | petab.v2.Problem


def get_problem_yaml_path(id_: str) -> Path:
    """Get the path to the PEtab problem YAML file.

    Parameters
    ----------
    id_: Problem name, as in `benchmark_models_petab.MODELS`.

    Returns
    -------
    The path to the PEtab problem YAML file.
    """
    yaml_path = Path(MODELS_DIR, id_, id_ + ".yaml")
    if not yaml_path.exists():
        yaml_path = Path(MODELS_DIR, id_, "problem.yaml")
    if not yaml_path.exists():
        raise ValueError(f"Could not find YAML for problem with ID `{id_}`.")
    return yaml_path


def get_problem(id_: str) -> Problem:
    """Read PEtab problem from the benchmark collection by name.

    Parameters
    ----------
    id_: Problem name, as in `benchmark_models_petab.MODELS`.

    Returns
    -------
    The PEtab problem (a ``petab.v1`` or ``petab.v2`` problem, depending on
    the problem's ``format_version``).
    """
    yaml_file = get_problem_yaml_path(id_)
    if get_major_version(yaml_file) >= 2:
        return petab.v2.Problem.from_yaml(yaml_file)
    return petab.v1.Problem.from_yaml(yaml_file)


def get_simulation_df(id_: str) -> pd.DataFrame | None:
    """Get the simulation dataframe for the benchmark collection problem with
    the given name.

    Parameters
    ----------
    id_: Problem name, as in `benchmark_models_petab.MODELS`.

    Returns
    -------
    The simulation dataframe if it exists, else None.
    """
    for filename in (f"simulatedData_{id_}.tsv", "simulations.tsv"):
        if (path := Path(MODELS_DIR, id_, filename)).is_file():
            return petab.v1.get_simulation_df(path)

    return None
