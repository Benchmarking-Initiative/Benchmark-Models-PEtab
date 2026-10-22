"""Tests for former problem IDs."""

import pytest

import benchmark_models_petab as models
from benchmark_models_petab.overview import get_readme_table


def test_renamed_models_are_not_problems():
    """Former IDs are no separate problems, their replacements exist."""
    assert not set(models.RENAMED_MODELS) & set(models.MODELS)
    assert not set(models.RENAMED_MODELS) & set(models.v1.MODELS)
    assert not set(models.RENAMED_MODELS) & set(models.v2.MODELS)
    assert set(models.RENAMED_MODELS.values()) <= set(models.MODELS)

    table = get_readme_table()
    for old_id in models.RENAMED_MODELS:
        assert old_id not in table


@pytest.mark.parametrize(
    "old_id,new_id",
    [("Schwen_PONE2014", "Schwen_PLoSOne2015")],
)
def test_former_id_is_accepted_with_warning(old_id, new_id):
    for version in (models.v1, models.v2):
        with pytest.warns(FutureWarning, match=new_id):
            path = version.get_problem_yaml_path(old_id)
        assert path == version.get_problem_yaml_path(new_id)
    with pytest.warns(FutureWarning, match=new_id):
        problem = models.get_problem(old_id)
    assert problem.model.model_id == new_id
    with pytest.warns(FutureWarning, match=new_id):
        assert models.get_simulation_df(old_id) is not None
    with pytest.warns(FutureWarning, match=new_id):
        assert models.get_metadata(old_id) == models.get_metadata(new_id)
