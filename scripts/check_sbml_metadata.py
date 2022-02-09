#!/usr/bin/env python3

from pathlib import Path
import sys

import petab

from lxml import etree
from more_itertools import one

from model_info import get_reference_uris
from _helpers import petab_yamls


num_failures = 0

for petab_problem_id, petab_yaml in petab_yamls.items():
    petab_problem = petab.Problem.from_yaml(petab_yaml)

    model_id = petab_problem.sbml_model.getId()
    model_name = petab_problem.sbml_model.getName()
    reference_uris = get_reference_uris(sbml_model=petab_problem.sbml_model)

    errors = []

    if model_id != petab_problem_id:
        errors.append(
            'Please change the model ID to match the problem ID.'
        )

    if model_name != petab_problem_id:
        errors.append(
            'Please change the model name to match the problem ID.'
        )

    if not reference_uris:
        errors.append(
            'Please add relevant references (e.g. the paper) to the model.'
        )

    errors = ['\t' + error for error in errors]

    print(petab_problem_id)
    if errors:
        print('\n'.join(errors))
        num_failures += 1
    print('='*100)  # just for output readability

num_passed = len(petab_yamls) - num_failures
print(f'Result: {Path(__file__).stem}')
print(f"{num_passed} out of {len(petab_yamls)} passed.")
print(f"{num_failures} out of {len(petab_yamls)} failed.")
# Fail unless all models passed
sys.exit(num_failures)
