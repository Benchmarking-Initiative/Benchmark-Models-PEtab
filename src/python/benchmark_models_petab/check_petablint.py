import os
import sys
from pathlib import Path

from . import MODELS, get_problem_yaml_path


def main():
    """Check all PEtab problems with petablint."""
    num_failures = 0

    for petab_problem_id in MODELS:
        print(petab_problem_id)
        petab_yaml = get_problem_yaml_path(petab_problem_id)
        ret = os.system(f"petablint -v {petab_yaml}")
        print("=" * 100)  # just for output readability

        if ret:
            num_failures += 1

    num_passed = len(MODELS) - num_failures
    print(f"Result: {Path(__file__).stem}")
    print(f"{num_passed} out of {len(MODELS)} passed.")
    print(f"{num_failures} out of {len(MODELS)} failed.")
    # Fail unless all models passed
    sys.exit(num_failures)
