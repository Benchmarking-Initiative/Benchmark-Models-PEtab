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
