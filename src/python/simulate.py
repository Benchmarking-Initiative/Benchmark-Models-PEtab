#!/usr/bin/env python3
"""
Script to simulate a model using AMICI.

Basic usage: simulate.py <problem_id>
Use ``--check-simulations`` to compare the simulations against the
simulation table of the problem (``v1/simulations.tsv``); the script then
exits with a non-zero status if they differ.
See --help for more options.
"""

import copy
import os
import sys
import argparse
import benchmark_models_petab
import amici.sim.sundials as ass
from amici.importers.petab.v1 import import_petab_problem
from amici.sim.sundials.petab.v1 import (
    rdatas_to_simulation_df,
    simulate_petab,
    LLH,
    RDATAS,
)
import logging
from pathlib import Path

import numpy as np
import yaml
import pandas as pd
import petab.v1 as petab
import petab.v1.C as petab_C
from petab.v1.lint import measurement_table_has_timepoint_specific_mappings
from petab.v1.core import flatten_timepoint_specific_output_overrides

#: Columns that identify a row of a measurement/simulation table.
KEY_COLUMNS = [
    petab_C.OBSERVABLE_ID,
    petab_C.PREEQUILIBRATION_CONDITION_ID,
    petab_C.SIMULATION_CONDITION_ID,
    petab_C.TIME,
]
#: Significant digits of the time points used to match rows; some
#: simulation tables carry the time points with more digits than the
#: measurement tables.
TIME_SIGNIFICANT_DIGITS = 6
#: Relative and absolute tolerance of the comparison to the simulation
#: tables (``--check-simulations``), see :func:`numpy.isclose`. Looser than
#: the solver tolerances, as the tables were made with different tools and
#: settings.
COMPARISON_RTOL = 1e-3
COMPARISON_ATOL = 1e-6
#: Default and problem-specific solver settings.
SOLVER_SETTINGS_FILE = Path(__file__).with_name("solver_settings.yaml")
#: For ``--check-simulation-tolerances``, which checks that the solver
#: tolerances used to reproduce the simulations are tight enough to ensure
#: sufficient accuracy: the factor by which the tolerances are made
#: stricter, and the largest acceptable relative change of the simulations
#: and of the log-likelihood; 100 times below :data:`COMPARISON_RTOL`.
TOLERANCE_CHECK_FACTOR = 100
TOLERANCE_CHECK_RTOL = 1e-5


def parse_cli_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Simulate a model using AMICI."
    )
    parser.add_argument(
        "problem_id",
        type=str,
        help="Identifier for the problem/model to simulate.",
    )
    parser.add_argument(
        "-j",
        dest="num_threads",
        nargs="?",
        default=None,
        const="all",
        help=(
            "Number of cores to use. "
            "`-j` (no value) uses all available cores. "
            "If omitted, threading is left unchanged."
        ),
    )
    parser.add_argument(
        "--check-simulations",
        action="store_true",
        help=(
            "Compare the simulations against the simulation table of the "
            "problem and exit with status 1 if they differ or if the "
            "problem has no simulation table."
        ),
    )
    parser.add_argument(
        "--check-simulation-tolerances",
        action="store_true",
        help=(
            "Check that the solver tolerances are strict enough: simulate "
            "again with stricter tolerances and exit with status 1 if the "
            "simulations or the log-likelihood change substantially."
        ),
    )
    parser.add_argument(
        "--all-conditions",
        action="store_true",
        help=(
            "Simulate all conditions, also for problems with `conditions` "
            "in the solver settings, for which by default only a subset of "
            "the conditions is simulated (always all with --output)."
        ),
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Write the simulations as PEtab simulation table to this file.",
    )
    args = parser.parse_args()

    args.num_threads = (
        os.cpu_count()
        if args.num_threads == "all"
        else 1
        if args.num_threads is None
        else max(1, int(args.num_threads))
    )

    return args


def _row_keys(df: pd.DataFrame) -> pd.DataFrame:
    """Get the columns that identify the rows of a measurement/simulation
    table, normalized for matching rows of different tables.

    Rows with identical keys (e.g. replicates) are told apart by their
    order of appearance.
    """
    keys = pd.DataFrame(index=df.index)
    for column in KEY_COLUMNS:
        if column == petab_C.TIME:
            keys[column] = [
                f"{float(t):.{TIME_SIGNIFICANT_DIGITS}g}" for t in df[column]
            ]
        elif column in df:
            keys[column] = [
                "" if pd.isna(value) else str(value) for value in df[column]
            ]
        else:
            keys[column] = ""
    keys["replicate"] = keys.groupby(KEY_COLUMNS).cumcount()
    return keys


def unflatten_observable_ids(
    simulation_df: pd.DataFrame, observable_ids
) -> pd.DataFrame:
    """Replace observable IDs of a flattened problem by the original ones.

    Simulation tables of problems with timepoint-specific overrides may use
    the observable IDs of the flattened problem,
    ``<observableId>__<overrides>__<conditions>``, see
    :func:`petab.v1.core.flatten_timepoint_specific_output_overrides`.
    """
    observable_ids = sorted(observable_ids, key=len, reverse=True)

    def unflatten(id_):
        if id_ in observable_ids:
            return id_
        for observable_id in observable_ids:
            if id_.startswith(f"{observable_id}__"):
                return observable_id
        return id_

    if petab_C.OBSERVABLE_ID not in simulation_df:
        return simulation_df
    simulation_df = simulation_df.copy()
    simulation_df[petab_C.OBSERVABLE_ID] = [
        unflatten(str(id_)) for id_ in simulation_df[petab_C.OBSERVABLE_ID]
    ]
    return simulation_df


def compare_simulations(
    simulation_df: pd.DataFrame,
    expected_df: pd.DataFrame,
    rtol: float = COMPARISON_RTOL,
    atol: float = COMPARISON_ATOL,
) -> bool:
    """Compare simulations against a reference simulation table.

    Parameters
    ----------
    simulation_df:
        The simulations. Must have the column ``simulation`` and the columns
        of :data:`KEY_COLUMNS`.
    expected_df:
        The reference simulation table.
    rtol, atol:
        Relative and absolute tolerance, see :func:`numpy.isclose`.

    Returns
    -------
    Whether the simulations agree.
    """
    for column in [petab_C.OBSERVABLE_ID, petab_C.SIMULATION_CONDITION_ID]:
        if column not in expected_df:
            print(f"The simulation table has no column `{column}`.")
            return False

    actual = _row_keys(simulation_df)
    actual["actual"] = simulation_df[petab_C.SIMULATION].to_numpy(float)
    expected = _row_keys(expected_df)
    expected["expected"] = pd.to_numeric(
        expected_df[petab_C.SIMULATION], errors="coerce"
    ).to_numpy(float)

    merged = actual.merge(
        expected,
        on=KEY_COLUMNS + ["replicate"],
        how="outer",
        indicator=True,
        sort=False,
    )
    ok = True

    for side, description in [
        ("left_only", "simulated, but not in the simulation table"),
        ("right_only", "in the simulation table, but not simulated"),
    ]:
        unmatched = merged[merged["_merge"] == side]
        if not unmatched.empty:
            ok = False
            print(f"{len(unmatched)} rows {description}, e.g.:")
            print(unmatched[KEY_COLUMNS].head().to_string(index=False))
            print()

    both = merged[merged["_merge"] == "both"]
    close = np.isclose(
        both["actual"], both["expected"], rtol=rtol, atol=atol, equal_nan=True
    )
    if not close.all():
        ok = False
        mismatches = both[~close].copy()
        mismatches["abs_diff"] = (
            mismatches["actual"] - mismatches["expected"]
        ).abs()
        mismatches["rel_diff"] = mismatches["abs_diff"] / mismatches[
            "expected"
        ].abs().replace(0, np.nan)
        print(
            f"{len(mismatches)} of {len(both)} simulations differ "
            f"(rtol={rtol}, atol={atol}); largest differences:"
        )
        print(
            mismatches.sort_values("abs_diff", ascending=False)[
                KEY_COLUMNS + ["actual", "expected", "abs_diff", "rel_diff"]
            ]
            .head(10)
            .to_string(index=False)
        )
        print()

    if ok:
        print(
            f"All {len(both)} simulations agree with the simulation table "
            f"(rtol={rtol}, atol={atol})."
        )
    return ok


def select_conditions(problem, measurement_df: pd.DataFrame, n: int):
    """Restrict a problem to ``n`` of its simulation conditions.

    The conditions are evenly spaced in the order of
    :func:`petab.v1.get_simulation_conditions`.

    Parameters
    ----------
    problem:
        The PEtab problem the AMICI model was imported from, possibly
        flattened.
    measurement_df:
        The measurement table of the original problem (before flattening).
    n:
        The number of conditions.

    Returns
    -------
    A copy of ``problem`` and ``measurement_df`` with only the measurements
    of the selected conditions, and the selected conditions.
    """
    conditions = petab.get_simulation_conditions(problem.measurement_df)
    if n >= len(conditions):
        return problem, measurement_df, conditions
    selected = conditions.iloc[
        np.unique(np.linspace(0, len(conditions) - 1, n).round().astype(int))
    ]
    columns = list(selected.columns)
    in_selected = (
        problem.measurement_df[columns]
        .merge(selected, how="left", indicator=True)["_merge"]
        .eq("both")
        .to_numpy()
    )
    index = problem.measurement_df.index[in_selected]

    problem = copy.copy(problem)
    problem.measurement_df = problem.measurement_df.loc[index]
    return problem, measurement_df.loc[index], selected


def get_solver_settings(problem_id: str) -> dict:
    """Get the solver settings for a problem.

    The defaults of :data:`SOLVER_SETTINGS_FILE`, updated by the settings
    for the problem, if any.
    """
    with open(SOLVER_SETTINGS_FILE) as f:
        settings = yaml.safe_load(f)
    return {
        **settings["default"],
        **(settings.get("problems") or {}).get(problem_id, {}),
    }


def simulate(
    problem,
    model,
    measurement_df: pd.DataFrame,
    settings: dict,
    num_threads: int = 1,
    verbose: bool = True,
):
    """Simulate a PEtab problem at the nominal parameters.

    Parameters
    ----------
    problem:
        The PEtab problem the AMICI model was imported from, possibly
        flattened.
    model:
        The AMICI model.
    measurement_df:
        The measurement table of the original problem (before flattening).
    settings:
        The solver settings, see :data:`SOLVER_SETTINGS_FILE`.
    num_threads:
        Number of threads to simulate the conditions in parallel.
    verbose:
        Whether to print the log-likelihood of every condition.

    Returns
    -------
    The result of :func:`simulate_petab` and the simulations as PEtab
    simulation table, in the order and with the observable IDs of
    ``measurement_df``, or ``None`` if a simulation failed.
    """
    solver = model.create_solver()
    solver.set_return_data_reporting_mode(
        ass.RDataReporting.observables_likelihood
    )
    solver.set_relative_tolerance(settings["rtol"])
    solver.set_absolute_tolerance(settings["atol"])
    solver.set_max_steps(int(settings["max_steps"]))
    res = simulate_petab(
        problem, amici_model=model, solver=solver, num_threads=num_threads
    )

    if verbose:
        for rdata in res[RDATAS]:
            print(
                f"{rdata.id}: llh = {rdata.llh}, chi2 = {rdata.chi2}, "
                f"status = {rdata.status}"
            )
        print()

    failed = [rdata for rdata in res[RDATAS] if rdata.status != 0]
    if failed:
        print(
            f"The simulation of {len(failed)} conditions failed, e.g. "
            f"{failed[0].id} with status {failed[0].status}."
        )
        return res, None

    # The simulations in the order of the measurement table, with the
    # observable IDs of the original (not flattened) problem.
    simulation_df = rdatas_to_simulation_df(
        res[RDATAS], model, problem.measurement_df
    ).loc[measurement_df.index]
    simulation_df[petab_C.OBSERVABLE_ID] = measurement_df[
        petab_C.OBSERVABLE_ID
    ]
    return res, simulation_df


def check_tolerances(
    problem,
    model,
    measurement_df: pd.DataFrame,
    settings: dict,
    simulation_df: pd.DataFrame,
    llh: float,
    num_threads: int = 1,
) -> bool:
    """Check that the solver tolerances are strict enough.

    Simulates again with the tolerances divided by
    :data:`TOLERANCE_CHECK_FACTOR` and checks that neither the simulations
    nor the log-likelihood change by more than :data:`TOLERANCE_CHECK_RTOL`
    (relative to the largest absolute simulation of the observable, for the
    simulations).

    Returns
    -------
    Whether the tolerances are strict enough.
    """
    stricter = {
        **settings,
        "rtol": settings["rtol"] / TOLERANCE_CHECK_FACTOR,
        "atol": settings["atol"] / TOLERANCE_CHECK_FACTOR,
    }
    res_strict, simulation_df_strict = simulate(
        problem,
        model,
        measurement_df,
        stricter,
        num_threads=num_threads,
        verbose=False,
    )
    if simulation_df_strict is None:
        print(
            f"The simulation with stricter tolerances "
            f"(rtol={stricter['rtol']:g}, atol={stricter['atol']:g}) failed. "
            f"Increase max_steps for the problem in "
            f"{SOLVER_SETTINGS_FILE.name}."
        )
        print()
        return False
    llh_strict = res_strict[LLH]

    simulation = simulation_df[petab_C.SIMULATION].to_numpy(float)
    simulation_strict = simulation_df_strict[petab_C.SIMULATION].to_numpy(
        float
    )
    # scale of each observable, to judge the simulations close to zero
    scale = (
        pd.Series(np.abs(simulation_strict))
        .groupby(simulation_df[petab_C.OBSERVABLE_ID].to_numpy())
        .transform("max")
        .to_numpy()
    )
    error = np.abs(simulation - simulation_strict) / np.where(
        scale > 0, scale, 1.0
    )
    error[np.isnan(simulation) & np.isnan(simulation_strict)] = 0.0
    error[np.isnan(simulation) != np.isnan(simulation_strict)] = np.inf
    max_error = np.max(error, initial=0.0)
    llh_error = abs(llh - llh_strict) / max(abs(llh_strict), 1.0)
    if np.isnan(llh) and np.isnan(llh_strict):
        llh_error = 0.0
    elif np.isnan(llh) or np.isnan(llh_strict):
        llh_error = np.inf

    print(
        f"Tolerance check: rtol={settings['rtol']:g}, "
        f"atol={settings['atol']:g} vs. rtol={stricter['rtol']:g}, "
        f"atol={stricter['atol']:g}: "
        f"largest change of the simulations {max_error:.2e} (relative to "
        f"the observable), of the log-likelihood {llh_error:.2e} "
        f"({llh} vs. {llh_strict})."
    )
    ok = (
        max_error <= TOLERANCE_CHECK_RTOL and llh_error <= TOLERANCE_CHECK_RTOL
    )
    if not ok:
        print(
            f"The tolerances are not strict enough: the changes exceed "
            f"{TOLERANCE_CHECK_RTOL:g}. Set stricter tolerances for the "
            f"problem in {SOLVER_SETTINGS_FILE.name}."
        )
    print()
    return ok


def main():
    """Simulate a PEtab problem with AMICI using nominal parameter values."""
    args = parse_cli_args()

    # Import and simulate
    print(args.problem_id)
    print("-" * len(args.problem_id), flush=True)

    if args.problem_id not in benchmark_models_petab.MODELS:
        sys.exit(f"Unknown problem: {args.problem_id}")
    if args.problem_id not in benchmark_models_petab.v1.MODELS:
        # TODO: simulate PEtab v2 problems
        print("The problem has no PEtab v1 encoding, skipping it.")
        print()
        return

    problem = benchmark_models_petab.get_problem(args.problem_id)
    expected_df = benchmark_models_petab.get_simulation_df(args.problem_id)
    if args.check_simulations and expected_df is None:
        print(
            "The problem has no simulation table. Add one, e.g. with "
            "--output, see CONTRIBUTING.md."
        )
        print(f"FAILED: {args.problem_id}")
        print()
        sys.exit(1)

    settings = get_solver_settings(args.problem_id)
    print(f"Solver settings: {settings}")
    print()

    measurement_df = problem.measurement_df.copy()
    if measurement_table_has_timepoint_specific_mappings(
        problem.measurement_df,
    ):
        flatten_timepoint_specific_output_overrides(problem)

    model = import_petab_problem(
        problem, generate_sensitivity_code=False, verbose=logging.INFO
    )

    n_conditions = settings.pop("conditions", None)
    if (
        n_conditions is not None
        and not args.all_conditions
        and not args.output
    ):
        problem, measurement_df, conditions = select_conditions(
            problem, measurement_df, int(n_conditions)
        )
        print(
            f"Simulating {len(conditions)} of the conditions "
            f"(`conditions` in {SOLVER_SETTINGS_FILE.name}; use "
            "--all-conditions to simulate all)."
        )
        print()
        if expected_df is not None:
            # compare only the rows of the selected conditions
            columns = list(conditions.columns)
            keys = _row_keys(measurement_df)[columns].drop_duplicates()
            expected_df = expected_df.loc[
                _row_keys(expected_df)[columns]
                .merge(keys, how="left", indicator=True)["_merge"]
                .eq("both")
                .to_numpy()
            ]

    res, simulation_df = simulate(
        problem,
        model,
        measurement_df,
        settings,
        num_threads=args.num_threads,
    )
    print("Total log-likelihood:", res[LLH])
    print()
    if simulation_df is None:
        print(f"FAILED: {args.problem_id}")
        print()
        sys.exit(1)

    if args.output:
        simulation_df.to_csv(args.output, sep="\t", index=False)
        print(f"Wrote the simulations to {args.output}.")
        print()

    ok = True
    if args.check_simulation_tolerances:
        ok &= check_tolerances(
            problem,
            model,
            measurement_df,
            settings,
            simulation_df,
            res[LLH],
            num_threads=args.num_threads,
        )

    if args.check_simulations:
        expected_df = unflatten_observable_ids(
            expected_df, measurement_df[petab_C.OBSERVABLE_ID].unique()
        )
        ok &= compare_simulations(simulation_df, expected_df)
        print()

    if not ok:
        print(f"FAILED: {args.problem_id}")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
