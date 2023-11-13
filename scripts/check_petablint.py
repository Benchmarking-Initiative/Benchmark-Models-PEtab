#!/usr/bin/env python3

from pathlib import Path
import os
import sys

from _helpers import petab_yamls


num_failures = 0

for petab_problem_id, petab_yaml in petab_yamls.items():
    print(petab_problem_id)
    ret = os.system(f"petablint -vy {petab_yaml}")
    print('='*100)  # just for output readability

    if ret:
        num_failures += 1

num_passed = len(petab_yamls) - num_failures
print(f'Result: {Path(__file__).stem}')
print(f"{num_passed} out of {len(petab_yamls)} passed.")
print(f"{num_failures} out of {len(petab_yamls)} failed.")
# Fail unless all models passed
sys.exit(num_failures)
