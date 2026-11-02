#!/usr/bin/env python3
"""
Script to simulate a model using AMICI.

Basic usage: simulate.py <problem_id>
Use ``--check`` to compare the simulations against the simulation table of
the problem (``v1/simulations.tsv``); the script then exits with a non-zero
status if they differ.
See --help for more options.
"""

import os
import sys
import argparse
import benchmark_models_petab
import amici.sim.sundials as ass
from amici.importers.petab.v1 import (
    import_petab_problem,
    rdatas_to_simulation_df,
    simulate_petab,
    LLH,
    RDATAS,
)
import logging
import numpy as np
import pandas as pd
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
        "--check",
        action="store_true",
        help=(
            "Compare the simulations against the simulation table of the "
            "problem and exit with status 1 if they differ. Problems "
            "without a simulation table are skipped."
        ),
    )
    parser.add_argument(
        "--rtol",
        type=float,
        default=1e-3,
        help="Relative tolerance for --check (default: %(default)s).",
    )
    parser.add_argument(
        "--atol",
        type=float,
        default=1e-6,
        help="Absolute tolerance for --check (default: %(default)s).",
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
    rtol: float,
    atol: float,
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


def main():
    """Simulate a PEtab problem with AMICI using nominal parameter values."""
    args = parse_cli_args()

    # Import and simulate
    print(args.problem_id)
    print("-" * len(args.problem_id), flush=True)

    problem = benchmark_models_petab.get_problem(args.problem_id)
    expected_df = benchmark_models_petab.get_simulation_df(args.problem_id)
    if args.check and expected_df is None:
        print("No simulation table, skipping the simulation.")
        print()
        return

    original_measurement_df = problem.measurement_df.copy()
    flattened = measurement_table_has_timepoint_specific_mappings(
        problem.measurement_df,
    )
    if flattened:
        flatten_timepoint_specific_output_overrides(problem)

    model = import_petab_problem(
        problem, generate_sensitivity_code=False, verbose=logging.INFO
    )
    solver = model.create_solver()
    solver.set_return_data_reporting_mode(
        ass.RDataReporting.observables_likelihood
    )
    res = simulate_petab(
        problem, model, solver=solver, num_threads=args.num_threads
    )

    for rdata in res[RDATAS]:
        print(
            f"{rdata.id}: llh = {rdata.llh}, chi2 = {rdata.chi2}, status = {rdata.status}"
        )

    print()
    print("Total log-likelihood:", res[LLH])
    print()

    if not (args.check or args.output):
        return

    # The simulations in the order of the measurement table, with the
    # observable IDs of the original (not flattened) problem.
    simulation_df = rdatas_to_simulation_df(
        res[RDATAS], model, problem.measurement_df
    ).loc[original_measurement_df.index]
    if flattened:
        simulation_df[petab_C.OBSERVABLE_ID] = original_measurement_df[
            petab_C.OBSERVABLE_ID
        ]

    if args.output:
        simulation_df.to_csv(args.output, sep="\t", index=False)
        print(f"Wrote the simulations to {args.output}.")
        print()

    if not args.check:
        return

    expected_df = unflatten_observable_ids(
        expected_df, original_measurement_df[petab_C.OBSERVABLE_ID].unique()
    )
    if not compare_simulations(
        simulation_df, expected_df, rtol=args.rtol, atol=args.atol
    ):
        print(f"FAILED: {args.problem_id}")
        print()
        sys.exit(1)
    print()


if __name__ == "__main__":
    main()
