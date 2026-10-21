#!/usr/bin/env python3
"""Convert benchmark problems from PEtab v1 to v2.

Converts all problems without a v2 encoding (except those in `SKIP`), or the
given problems, with `petab.v2.petab1to2`. All estimated log-scaled
parameters are reparametrized (see `petab.v2.reparametrize_log`). Existing
v2 encodings are only replaced if requested explicitly.

Usage: v1_v2.py [--overwrite] [PROBLEM_ID ...]
"""

import argparse
import logging
import shutil
import warnings
from pathlib import Path

import petab.v2
from petab.v2.petab1to2 import petab1to2

import benchmark_models_petab as bmp
from benchmark_models_petab.C import MODELS_DIR, V2_DIRNAME

logger = logging.getLogger(__name__)

#: Problems not converted by default, with reasons.
SKIP = {
    "Froehlich_CellSystems2018": "the generated condition table is huge",
}


def convert(problem_id: str, output_dir: Path) -> None:
    """Convert a PEtab v1 problem to v2."""
    logger.info(f"Converting {problem_id}...")
    # petab1to2 doesn't replace existing files
    shutil.rmtree(output_dir, ignore_errors=True)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        petab1to2(
            bmp.v1.get_problem_yaml_path(problem_id),
            output_dir,
            reparametrize="all",
        )
    for w in caught:
        logger.warning(f"{problem_id}: {w.message}")


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("problem_ids", nargs="*", metavar="PROBLEM_ID")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace existing v2 encodings.",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    petab.v2.set_options(table_columns="non_empty")

    for problem_id in args.problem_ids or bmp.MODELS:
        if not args.problem_ids and problem_id in SKIP:
            logger.info(f"Skipping {problem_id}: {SKIP[problem_id]}.")
            continue
        if problem_id in bmp.v2.MODELS and not args.overwrite:
            logger.info(f"Skipping {problem_id}: v2 encoding exists.")
            continue
        convert(problem_id, Path(MODELS_DIR, problem_id, V2_DIRNAME))


if __name__ == "__main__":
    main()
