"""Tests for the v2 accessors.

No problem in the collection has a `v2/` encoding yet, so only the
"not found" error path can be tested here. Once real `problems/<id>/v2/`
directories exist, add a happy-path test (`get_problem`/`get_simulation_df`
on an actual v2 problem) alongside these.
"""

import pytest

import benchmark_models_petab as models


def test_get_problem_yaml_path_raises_for_missing_v2():
    with pytest.raises(ValueError, match="v2"):
        models.v2.get_problem_yaml_path(models.MODELS[0])


def test_get_problem_raises_for_missing_v2():
    with pytest.raises(ValueError, match="v2"):
        models.v2.get_problem(models.MODELS[0])


def test_get_simulation_df_returns_none_for_missing_v2():
    assert models.v2.get_simulation_df(models.MODELS[0]) is None
