#!/usr/bin/env python3
"""
Script to simulate a model using AMICI.

Handles both PEtab v1 and PEtab v2 problems (see :func:`simulate`).

Basic usage: simulate.py <problem_id>
See --help for more options.
"""

import argparse
import logging
import os

import amici.sim.sundials as ass
import benchmark_models_petab
import petab.v2
from amici.importers.petab import PetabImporter
from amici.importers.petab.v1 import import_petab_problem
from amici.sim.sundials.petab.v1 import LLH, RDATAS, simulate_petab
from petab.v1.core import flatten_timepoint_specific_output_overrides
from petab.v1.lint import measurement_table_has_timepoint_specific_mappings


def _relax_tolerances(solver) -> None:
    """Loosen AMICI's very tight default absolute tolerance.

    The default ``atol`` (1e-16) can trigger a too-small step size right after
    a PEtab experiment-period state change; 1e-12 is robust while remaining
    accurate.
    """
    solver.set_relative_tolerance(1e-10)
    solver.set_absolute_tolerance(1e-12)
    solver.set_max_steps(10**6)


def create_v2_simulator(
    problem: "petab.v2.Problem",
    *,
    num_threads: int = 1,
    verbose: int = logging.INFO,
):
    """Create an AMICI PEtab simulator for a PEtab v2 problem.

    The importer encodes the experiment periods (e.g. cycle resets) as events,
    so simulating the problem applies them automatically.
    """
    importer = PetabImporter(problem, verbose=verbose)
    simulator = importer.create_simulator()
    simulator.num_threads = num_threads
    _relax_tolerances(simulator.solver)
    return simulator


def _simulate_v1(problem, num_threads):
    """Simulate a PEtab v1 problem; returns (total_llh, rdatas)."""
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
        problem, amici_model=model, solver=solver, num_threads=num_threads
    )
    return res[LLH], res[RDATAS]


def _simulate_v2(problem, num_threads):
    """Simulate a PEtab v2 problem; returns (total_llh, rdatas)."""
    simulator = create_v2_simulator(problem, num_threads=num_threads)
    res = simulator.simulate()
    return res.llh, res.rdatas


def simulate(problem, num_threads: int = 1):
    """Simulate a PEtab problem at its nominal parameters with AMICI.

    Dispatches to the PEtab v1 or v2 simulation route depending on the type of
    ``problem``. Returns ``(total_log_likelihood, rdatas)``.
    """
    if isinstance(problem, petab.v2.Problem):
        return _simulate_v2(problem, num_threads)
    return _simulate_v1(problem, num_threads)


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

    total_llh, rdatas = simulate(problem, num_threads=args.num_threads)

    for rdata in rdatas:
        chi2 = getattr(rdata, "chi2", None)
        print(
            f"{rdata.id}: llh = {rdata.llh}, chi2 = {chi2}, "
            f"status = {rdata.status}"
        )

    print()
    print("Total log-likelihood:", total_llh)
    print()


if __name__ == "__main__":
    main()
