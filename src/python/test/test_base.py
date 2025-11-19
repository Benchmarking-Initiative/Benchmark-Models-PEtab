"""Basic tests."""

import benchmark_models_petab as models


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
