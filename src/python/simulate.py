#!/usr/bin/env python3
"""
Script to simulate a model using AMICI.

Basic usage: simulate.py <problem_id>
See --help for more options.
"""

import os
import argparse
import benchmark_models_petab
import amici.sim.sundials as ass
from amici.importers.petab.v1 import (
    import_petab_problem,
    simulate_petab,
    LLH,
    RDATAS,
)
import logging
from petab.v1.lint import measurement_table_has_timepoint_specific_mappings
from petab.v1.core import flatten_timepoint_specific_output_overrides


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
    args = parser.parse_args()

    args.num_threads = (
        os.cpu_count()
        if args.num_threads == "all"
        else 1
        if args.num_threads is None
        else max(1, int(args.num_threads))
    )

    return args


def main():
    """Simulate a PEtab problem with AMICI using nominal parameter values."""
    args = parse_cli_args()

    # Import and simulate
    print(args.problem_id)
    print("-" * len(args.problem_id), flush=True)

    problem = benchmark_models_petab.get_problem(args.problem_id)

    if measurement_table_has_timepoint_specific_mappings(
        problem.measurement_df,
    ):
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


if __name__ == "__main__":
    main()
