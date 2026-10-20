"""Tests for the v2 accessors."""

import pytest

import benchmark_models_petab as models

NO_V2_PROBLEM_ID = "NotAProblem_2000"


def test_get_problem_yaml_path_raises_for_missing_v2():
    with pytest.raises(ValueError, match="v2"):
        models.v2.get_problem_yaml_path(NO_V2_PROBLEM_ID)


def test_get_problem_raises_for_missing_v2():
    with pytest.raises(ValueError, match="v2"):
        models.v2.get_problem(NO_V2_PROBLEM_ID)


def test_get_simulation_df_returns_none_for_missing_v2():
    assert models.v2.get_simulation_df(NO_V2_PROBLEM_ID) is None


def test_get_problem_yaml_path():
    path = models.v2.get_problem_yaml_path("Boehm_JProteomeRes2014")
    assert path.is_file()


def test_get_problem():
    problem = models.v2.get_problem("Boehm_JProteomeRes2014")
    assert "log10_k_phos" in problem.parameter_df.index
    assert "k_phos" not in problem.parameter_df.index
    assert len(problem.measurement_df) > 0


def test_models():
    assert "Boehm_JProteomeRes2014" in models.v2.MODELS
    assert set(models.v2.MODELS) <= set(models.MODELS)
