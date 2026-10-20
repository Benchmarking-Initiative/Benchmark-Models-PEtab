"""Tests for the README overview table."""

import benchmark_models_petab as models
from benchmark_models_petab.overview import get_readme_table

PROBLEM_ID = "Boehm_JProteomeRes2014"


def test_get_readme_table():
    table = get_readme_table()
    (row,) = [line for line in table.splitlines() if f"[{PROBLEM_ID}]" in line]
    assert models.get_metadata(PROBLEM_ID).short_description in row
    assert f"[v1](problems/{PROBLEM_ID}/v1/)" in row
    assert f"[v2](problems/{PROBLEM_ID}/v2/)" in row
    # a problem without a v2 encoding
    no_v2 = next(id_ for id_ in models.MODELS if id_ not in models.v2.MODELS)
    (row,) = [line for line in table.splitlines() if f"[{no_v2}]" in line]
    assert "/v2/" not in row
