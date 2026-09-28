"""Check that every YAML file in the `problems/` directory that looks like a
PEtab problem actually passes petablint.

This catches broken PEtab problems anywhere under `problems/`, for example,
supplementary problem definitions kept in a problem's `resources/`.
"""

import os
import sys
from pathlib import Path

import petab.v1 as petab
import yaml

from .C import MODELS_DIR


def looks_like_petab_yaml(path: Path) -> bool:
    """Heuristically check whether a YAML file looks like a PEtab v1 problem
    YAML."""
    try:
        with open(path) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError:
        return False
    return (
        isinstance(data, dict)
        and petab.FORMAT_VERSION in data
        and petab.PROBLEMS in data
    )


def main():
    """Check all PEtab-looking YAML files under `problems/` with petablint."""
    yaml_files = sorted(
        {*Path(MODELS_DIR).rglob("*.yaml"), *Path(MODELS_DIR).rglob("*.yml")}
    )
    petab_yaml_files = [f for f in yaml_files if looks_like_petab_yaml(f)]

    num_failures = 0
    for petab_yaml in petab_yaml_files:
        print(petab_yaml.relative_to(MODELS_DIR), flush=True)
        ret = os.system(f"petablint -v {petab_yaml}")
        print("=" * 100, flush=True)

        if ret:
            num_failures += 1

    num_passed = len(petab_yaml_files) - num_failures
    print(f"Result: {Path(__file__).stem}")
    print(f"{num_passed} out of {len(petab_yaml_files)} passed.")
    print(f"{num_failures} out of {len(petab_yaml_files)} failed.")
    sys.exit(num_failures)
