"""Stats for the PEtab v2 encodings of the benchmark problems."""

from pathlib import Path

import libsbml
import numpy as np
import pandas as pd
import petab.v2 as petab

from . import v2
from .C import V2_DIRNAME
from .overview import column_descriptions as v1_column_descriptions
from .overview import columns as v1_columns
from .overview import (
    get_reference_uris,
    index_column,
    make_sbml4humans_urls,
    sbml_model_has_discontinuities,
)

_labels = v1_columns | {
    "experiments": "Experiments",
    "preequilibration": "Experiments with preequilibration",
    "prior_distributions": "Prior distribution(s)",
}

#: Column labels for the overview table, in column order.
columns = {
    col: _labels[col]
    for col in (
        "petab_problem_id",
        "experiments",
        "preequilibration",
        "postequilibration",
        "estimated_parameters",
        "measurements",
        "observables",
        "species",
        "events",
        "possible_discontinuities",
        "noise_distributions",
        "prior_distributions",
        "reference_uris",
        "sbml4humans_urls",
    )
}

#: Column descriptions for the overview table.
column_descriptions = v1_column_descriptions | {
    "experiments": (
        "Number of experiments in the measurement table. Measurements "
        "without an experiment count as one."
    ),
    "preequilibration": (
        "Number of experiments with a preequilibration period."
    ),
    "postequilibration": (
        "Number of experiments with steady-state measurements (time = inf)."
    ),
    "noise_distributions": "Noise distributions of the observables.",
    "prior_distributions": "Prior distributions of estimated parameters.",
    "possible_discontinuities": (
        "Heuristic: events with assignments, discontinuous functions "
        "(piecewise, min, max, ...) with time-dependent arguments in the "
        "model, or condition changes after the start of an experiment."
    ),
}


def get_summary(problem: petab.Problem, petab_problem_id: str) -> dict:
    """Get dictionary with stats for the given PEtab v2 problem.

    Measurements without an experiment ID count as one experiment.
    Preequilibration and postequilibration are counted as the number of
    experiments with a preequilibration period (starting at ``-inf``) or
    with steady-state measurements (at ``inf``), respectively.
    For problems with multiple models, species and events are the maximum
    over the models, and references are collected from all models.
    """
    sbml_models = get_sbml_models(problem)
    experiments = {e.id: e for e in problem.experiments}
    measured_experiment_ids = {m.experiment_id for m in problem.measurements}

    return {
        "petab_problem_id": petab_problem_id,
        "experiments": len(measured_experiment_ids),
        "preequilibration": sum(
            experiments[exp_id].has_preequilibration
            for exp_id in measured_experiment_ids
            if exp_id is not None
        ),
        "postequilibration": len(
            {m.experiment_id for m in problem.measurements if m.time == np.inf}
        ),
        "estimated_parameters": problem.n_estimated,
        "measurements": len(problem.measurements),
        "observables": len({m.observable_id for m in problem.measurements}),
        "species": max(m.getNumSpecies() for m in sbml_models),
        "events": max(m.getNumEvents() for m in sbml_models),
        "possible_discontinuities": (
            any(sbml_model_has_discontinuities(m) for m in sbml_models)
            or any(
                has_period_changes(experiments[exp_id])
                for exp_id in measured_experiment_ids
                if exp_id is not None
            )
        ),
        "noise_distributions": "; ".join(
            sorted({str(o.noise_distribution) for o in problem.observables})
        ),
        "prior_distributions": "; ".join(
            sorted(
                {
                    str(p.prior_distribution)
                    for p in problem.parameters
                    if p.estimate and p.prior_distribution is not None
                }
            )
        ),
        "reference_uris": list(
            dict.fromkeys(
                uri for m in sbml_models for uri in get_reference_uris(m)
            )
        ),
        "sbml4humans_urls": make_sbml4humans_urls(
            petab_problem_id,
            V2_DIRNAME,
            [Path(m.rel_path).as_posix() for m in problem.models],
        ),
    }


def get_sbml_models(problem: petab.Problem) -> list[libsbml.Model]:
    """Get the SBML models of the problem.

    :raises ValueError: If the problem has no model or a non-SBML model.
    """
    if not problem.models:
        raise ValueError("The problem has no model.")
    if non_sbml := [m.model_id for m in problem.models if m.type_id != "sbml"]:
        raise ValueError(f"Only SBML models are supported, not: {non_sbml}")
    return [m.sbml_model for m in problem.models]


def has_period_changes(experiment: petab.Experiment) -> bool:
    """Check whether the experiment changes conditions after its start.

    Preequilibration periods are not considered.
    """
    return (
        sum(not period.is_preequilibration for period in experiment.periods)
        > 1
    )


def get_overview_df() -> pd.DataFrame:
    """Get overview table with stats for all PEtab v2 benchmark problems."""
    data = [
        get_summary(v2.get_problem(petab_problem_id), petab_problem_id)
        for petab_problem_id in v2.MODELS
    ]
    df = pd.DataFrame(data, columns=list(columns))
    return df.set_index([index_column])
