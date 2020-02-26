#!/usr/bin/env python3

import os
import sys

model_list = os.scandir()
model_list = sorted(f.name for f in model_list if f.is_dir())

num_failures = 0

for benchmark_model in model_list:
    print(benchmark_model)
    ret = os.system(
        "cd {} && petablint -v -y {}.yaml ".format(
            benchmark_model, benchmark_model
        )
    )
    print('='*100)  # just for output readability

    if ret:
        num_failures += 1

num_passed = len(model_list) - num_failures

print(f"{num_passed} out of {len(model_list)} passed.")
print(f"{num_failures} out of {len(model_list)} failed.")

# Fail unless all models passed
sys.exit(num_failures)
