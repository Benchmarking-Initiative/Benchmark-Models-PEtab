"""Tests for the v2 overview table and the site's overview page data."""

import numpy as np
import pandas as pd
import petab.v2 as petab

import benchmark_models_petab as models
from benchmark_models_petab import overview, overview_v2
from benchmark_models_petab._site.build import (
    column_group,
    get_summary_tiles,
    get_table,
)

PROBLEM_ID = "Boehm_JProteomeRes2014"


def test_get_summary():
    summary = overview_v2.get_summary(
        models.v2.get_problem(PROBLEM_ID), PROBLEM_ID
    )
    assert set(summary) == set(overview_v2.columns)
    assert summary["experiments"] == 1
    assert summary["estimated_parameters"] == 9
    assert summary["measurements"] == 48
    assert summary["observables"] == 3
    assert summary["noise_distributions"] == "normal"
    assert summary["prior_distributions"] == ""
    assert summary["possible_discontinuities"] is False
    assert summary["sbml4humans_urls"][0].endswith(
        f"/{PROBLEM_ID}/v2/model.xml"
    )


def test_get_table():
    table = get_table(
        overview_v2.get_overview_df(),
        overview_v2.columns,
        overview_v2.column_descriptions,
        "v2",
    )
    kinds = {col["field"]: col["kind"] for col in table["columns"]}
    assert kinds["petab_problem_id"] == "id"
    assert kinds["short_description"] == "description"
    assert kinds["measurements"] == "int"
    assert kinds["possible_discontinuities"] == "bool"
    assert kinds["reference_uris"] == "links"
    assert kinds["noise_distributions"] == "tags"

    # columns of a group are contiguous, ungrouped columns come first
    groups = [col["group"] for col in table["columns"]]
    assert groups[:2] == [None, None]
    assert None not in groups[2:]
    for group in set(groups) - {None}:
        idx = [i for i, g in enumerate(groups) if g == group]
        assert idx == list(range(idx[0], idx[-1] + 1))
    assert all(col["tooltip"] for col in table["columns"])

    (row,) = [r for r in table["rows"] if r["petab_problem_id"] == PROBLEM_ID]
    assert (
        row["short_description"]
        == models.get_metadata(PROBLEM_ID).short_description
    )
    assert row["measurements"] == 48
    assert table["tree_url"].endswith("/problems/{id}/v2")


def test_has_period_changes():
    def experiment(*times):
        return petab.Experiment(
            id="e",
            periods=[petab.ExperimentPeriod(time=t) for t in times],
        )

    assert not overview_v2.has_period_changes(experiment(0))
    assert not overview_v2.has_period_changes(experiment(-np.inf, 0))
    assert overview_v2.has_period_changes(experiment(0, 10))
    assert overview_v2.has_period_changes(experiment(-np.inf, 0, 10))


def test_get_summary_tiles():
    v1_df = pd.DataFrame(
        {
            "estimated_parameters": [3, 1200],
            "measurements": [10, 27132],
            "conditions": [1, 9169],
            "observables": [1, 4],
        },
        index=["a", "b"],
    )
    # "b" is ignored, as it has a v1 encoding; "c" extends the ranges
    v2_df = pd.DataFrame(
        {
            "estimated_parameters": [1, 2],
            "measurements": [1, 30000],
            "experiments": [9170, 1],
            "observables": [5, 5],
        },
        index=["b", "c"],
    )
    tiles = {
        label: value for value, label, _ in get_summary_tiles(v1_df, v2_df)
    }
    assert tiles["problems in total"] == str(len(models.MODELS))
    assert tiles["in PEtab v1"] == str(len(models.v1.MODELS))
    assert tiles["in PEtab v2"] == str(len(models.v2.MODELS))
    assert tiles["measurements"] == "10\u201330,000"
    assert tiles["simulation conditions"] == "1\u20139,169"
    assert tiles["estimated parameters"] == "2\u20131,200"
    assert tiles["observables"] == "1\u20135"


def test_all_columns_grouped():
    for labels in (overview.columns, overview_v2.columns):
        assert set(labels) - set(column_group) == {"petab_problem_id"}
