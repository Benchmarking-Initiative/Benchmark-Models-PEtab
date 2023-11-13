"""Get a petab problem from the collection."""

import os

import petab

from .C import MODELS_DIR


def get_problem(id_: str) -> petab.Problem:
    """Read PEtab problem from benchmark collection by name.

    Parameters
    ----------
    id_: Problem name, as in `benchmark_models_petab.MODELS`.

    Returns
    -------
    The PEtab problem.
    """
    yaml_file = os.path.join(MODELS_DIR, id_, id_ + ".yaml")
    petab_problem = petab.Problem.from_yaml(yaml_file)
    return petab_problem
