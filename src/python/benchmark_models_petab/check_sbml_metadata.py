#!/usr/bin/env python3

import sys
from pathlib import Path

from . import MODELS, get_problem
from .overview import get_reference_uris


def main():
    """Check SBML metadata for all PEtab problems."""
    num_failures = 0

    for petab_problem_id in MODELS:
        petab_problem = get_problem(petab_problem_id)

        model_id = petab_problem.sbml_model.getId()
        model_name = petab_problem.sbml_model.getName()
        reference_uris = get_reference_uris(
            sbml_model=petab_problem.sbml_model
        )

        errors = []

        if model_id != petab_problem_id:
            errors.append(
                "Please change the model ID to match the problem ID."
            )

        if model_name != petab_problem_id:
            errors.append(
                "Please change the model name to match the problem ID."
            )

        if not reference_uris:
            errors.append(
                "Please add relevant references (e.g. the paper) to the model."
            )

        errors = ["\t" + error for error in errors]

        print(petab_problem_id)
        if errors:
            print("\n".join(errors))
            num_failures += 1
        print("=" * 100)  # just for output readability

    num_passed = len(MODELS) - num_failures
    print(f"Result: {Path(__file__).stem}")
    print(f"{num_passed} out of {len(MODELS)} passed.")
    print(f"{num_failures} out of {len(MODELS)} failed.")
    # Fail unless all models passed
    sys.exit(num_failures)
