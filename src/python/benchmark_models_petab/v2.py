"""Get a PEtab v2 problem from the collection."""

from pathlib import Path

import pandas as pd
import petab.v2 as petab

from .C import MODELS_DIR, PROBLEM_FILENAME, SIMULATIONS_FILENAME, V2_DIRNAME


def get_problem_yaml_path(id_: str) -> Path:
    """Get the path to the PEtab v2 problem YAML file.

    Parameters
    ----------
    id_: Problem name, as in `benchmark_models_petab.MODELS`.

    Returns
    -------
    The path to the PEtab v2 problem YAML file.
    """
    yaml_path = Path(MODELS_DIR, id_, V2_DIRNAME, PROBLEM_FILENAME)
    if not yaml_path.exists():
        raise ValueError(
            f"Could not find a v2 YAML for problem with ID `{id_}`. "
            "Most problems in this collection do not have a v2 encoding "
            "yet; see `benchmark_models_petab.v1` for the v1 problem."
        )
    return yaml_path


def get_problem(id_: str) -> petab.Problem:
    """Read the PEtab v2 problem from the benchmark collection by name.

    Parameters
    ----------
    id_: Problem name, as in `benchmark_models_petab.MODELS`.

    Returns
    -------
    The PEtab v2 problem.
    """
    yaml_file = get_problem_yaml_path(id_)
    return petab.Problem.from_yaml(yaml_file)


def get_simulation_df(id_: str) -> pd.DataFrame | None:
    """Get the simulation dataframe for the v2 encoding of the benchmark
    collection problem with the given name.

    Parameters
    ----------
    id_: Problem name, as in `benchmark_models_petab.MODELS`.

    Returns
    -------
    The simulation dataframe if it exists, else None.
    """
    path = Path(MODELS_DIR, id_, V2_DIRNAME, SIMULATIONS_FILENAME)
    if path.is_file():
        return pd.read_csv(
            path, sep="\t", index_col=None, float_precision="round_trip"
        )

    return None
