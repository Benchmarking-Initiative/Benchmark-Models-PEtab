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


# Per-problem AMICI solver overrides for PEtab v2 problems that need looser
# tolerances than AMICI's very tight defaults. Problems not listed here keep
# the AMICI defaults, so this is not applied globally to all v2 problems.
_V2_SOLVER_OVERRIDES = {
    # The cycle-reset state change makes this system stiff; the default
    # atol=1e-16 triggers a too-small step size right after a reset.
    "Cook_AIChE2022": dict(rtol=1e-10, atol=1e-12, max_steps=10**6),
}


def _apply_solver_settings(solver, solver_settings: dict | None) -> None:
    """Apply optional AMICI solver tolerance overrides.

    Leaves AMICI's defaults untouched when ``solver_settings`` is ``None``.
    Recognized keys: ``rtol``, ``atol``, ``max_steps``.
    """
    if not solver_settings:
        return
    if "rtol" in solver_settings:
        solver.set_relative_tolerance(solver_settings["rtol"])
    if "atol" in solver_settings:
        solver.set_absolute_tolerance(solver_settings["atol"])
    if "max_steps" in solver_settings:
        solver.set_max_steps(solver_settings["max_steps"])


def create_v2_simulator(
    problem: "petab.v2.Problem",
    *,
    num_threads: int = 1,
    verbose: int = logging.INFO,
    solver_settings: dict | None = None,
):
    """Create an AMICI PEtab simulator for a PEtab v2 problem.

    ``solver_settings`` optionally overrides the AMICI solver tolerances
    (keys ``rtol``, ``atol``, ``max_steps``); AMICI defaults are used when it
    is ``None``.
    """
    importer = PetabImporter(problem, verbose=verbose)
    simulator = importer.create_simulator()
    simulator.num_threads = num_threads
    _apply_solver_settings(simulator.solver, solver_settings)
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


def _simulate_v2(problem, num_threads, solver_settings=None):
    """Simulate a PEtab v2 problem; returns (total_llh, rdatas)."""
    simulator = create_v2_simulator(
        problem, num_threads=num_threads, solver_settings=solver_settings
    )
    res = simulator.simulate()
    return res.llh, res.rdatas


def simulate(
    problem, num_threads: int = 1, solver_settings: dict | None = None
):
    """Simulate a PEtab problem at its nominal parameters with AMICI.

    Dispatches to the PEtab v1 or v2 simulation route depending on the type of
    ``problem``. ``solver_settings`` (v2 only) optionally overrides the AMICI
    solver tolerances. Returns ``(total_log_likelihood, rdatas)``.
    """
    if isinstance(problem, petab.v2.Problem):
        return _simulate_v2(problem, num_threads, solver_settings)
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

    total_llh, rdatas = simulate(
        problem,
        num_threads=args.num_threads,
        solver_settings=_V2_SOLVER_OVERRIDES.get(args.problem_id),
    )

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
