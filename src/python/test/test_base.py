"""Basic tests."""

import pytest
import benchmark_models_petab as models
from petab.v1.calculate import calculate_llh
import pandas as pd


def test_constants():
    """Assert that constant values can be evaluated."""
    assert models.MODELS_DIR
    assert models.MODELS
    assert models.MODEL_DIRS


def test_get_problem():
    """Test whether extracting a petab problem works."""
    problem = models.get_problem(models.MODELS[0])
    assert problem.measurement_df is not None


def test_get_simulation_df():
    assert models.get_simulation_df("Elowitz_Nature2000").empty is False
    assert models.get_simulation_df("not a problem name") is None


@pytest.mark.parametrize("problem_id", models.MODELS)
def test_can_calculate_llh_from_simulation_df(problem_id):
    """Test whether log-likelihood can be calculated from the simulation df."""
    problem = models.get_problem(problem_id)
    sim_df = models.get_simulation_df(problem_id)

    if sim_df is None:
        pytest.skip(f"No simulation table for problem {problem_id}")

    try:
        calculate_llh(
            observable_dfs=problem.observable_df,
            measurement_dfs=problem.measurement_df,
            parameter_dfs=problem.parameter_df,
            simulation_dfs=sim_df,
        )
    except Exception:
        with pd.option_context(
            "display.max_rows",
            None,
            "display.max_columns",
            None,
            "display.width",
            1000,
        ):
            print("Simulation table:")
            print(sim_df)
            print("Measurement table:")
            print(problem.measurement_df)
        raise
