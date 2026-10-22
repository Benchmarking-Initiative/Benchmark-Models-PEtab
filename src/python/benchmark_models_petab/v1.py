"""Get a PEtab v1 problem from the collection."""

from pathlib import Path

import petab.v1 as petab

import pandas as pd

from ._ids import resolve_id
from .C import (
    MODELS as ALL_MODELS,
    MODELS_DIR,
    PROBLEM_FILENAME,
    SIMULATIONS_FILENAME,
    V1_DIRNAME,
)

#: IDs of the problems that have a PEtab v1 encoding.
MODELS: list[str] = [
    id_
    for id_ in ALL_MODELS
    if Path(MODELS_DIR, id_, V1_DIRNAME, PROBLEM_FILENAME).is_file()
]


def get_problem_yaml_path(id_: str) -> Path:
    """Get the path to the PEtab problem YAML file.

    Parameters
    ----------
    id_: Problem name, as in `benchmark_models_petab.MODELS`.

    Returns
    -------
    The path to the PEtab problem YAML file.
    """
    id_ = resolve_id(id_)
    yaml_path = Path(MODELS_DIR, id_, V1_DIRNAME, PROBLEM_FILENAME)
    if not yaml_path.exists():
        raise ValueError(
            f"Could not find a v1 YAML for problem with ID `{id_}`."
        )
    return yaml_path


def get_problem(id_: str) -> petab.Problem:
    """Read PEtab problem from the benchmark collection by name.

    Parameters
    ----------
    id_: Problem name, as in `benchmark_models_petab.MODELS`.

    Returns
    -------
    The PEtab problem.
    """
    yaml_file = get_problem_yaml_path(id_)
    petab_problem = petab.Problem.from_yaml(yaml_file)
    return petab_problem


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
    id_ = resolve_id(id_)
    path = Path(MODELS_DIR, id_, V1_DIRNAME, SIMULATIONS_FILENAME)
    if path.is_file():
        return petab.get_simulation_df(path)

    return None
