import os
import sys
from pathlib import Path

from . import MODELS, v1, v2
from .C import MODELS_DIR


def main():
    """Check all PEtab problems with petablint.

    Checks all encodings (`v1/`, `v2/`) of each problem. A problem without
    any encoding counts as a failure.
    """
    num_checked = 0
    num_failures = 0
    for petab_problem_id in MODELS:
        petab_yamls = []
        for version in (v1, v2):
            try:
                petab_yamls.append(
                    version.get_problem_yaml_path(petab_problem_id)
                )
            except ValueError:
                pass
        if not petab_yamls:
            print(f"{petab_problem_id}: no PEtab problem found", flush=True)
            num_checked += 1
            num_failures += 1

        for petab_yaml in petab_yamls:
            print(petab_yaml.relative_to(MODELS_DIR), flush=True)
            ret = os.system(f"petablint -v {petab_yaml}")
            print("=" * 100, flush=True)  # just for output readability

            num_checked += 1
            if ret:
                num_failures += 1

    num_passed = num_checked - num_failures
    print(f"Result: {Path(__file__).stem}")
    print(f"{num_passed} out of {num_checked} passed.")
    print(f"{num_failures} out of {num_checked} failed.")
    # Fail unless all problems passed
    sys.exit(num_failures)
