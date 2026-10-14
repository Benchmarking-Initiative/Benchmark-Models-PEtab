#!/usr/bin/env python3
"""Convert benchmark problems from PEtab v1 to v2 format."""

import logging
from pathlib import Path

import benchmark_models_petab
from petab.v2.petab1to2 import petab1to2


def main():
    logging.basicConfig(level=logging.INFO)

    for problem_id in benchmark_models_petab.MODELS:
        if problem_id == "Froehlich_CellSystems2018":
            # naive conversion generates huge condition table
            logging.warning("Skipping Froehlich_CellSystems2018 due to performance issues.")
            continue

        output_dir = Path(benchmark_models_petab.MODELS_DIR) / problem_id / "v2"
        convert(problem_id, output_dir=output_dir)

def convert(problem_id: str, output_dir: Path):
    """Convert a PEtab v1 problem to v2 format."""
    logging.info(f"Converting {problem_id}...")
    yaml_path = benchmark_models_petab.get_problem_yaml_path(problem_id)
    try:
        petab1to2(yaml_path, output_dir)
    except NotImplementedError as e:
        logging.warning(f"Skipping {problem_id}: {e}")
        return

    logging.info(f"Converted {problem_id}.")


if __name__ == "__main__":
    main()
