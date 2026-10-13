"""Check that every problem has a metadata file that matches the schema."""

import sys
from pathlib import Path

import pydantic
import yaml

from .C import MODELS
from .metadata import ProblemMetadata, get_metadata_path


def check_metadata_file(path: Path) -> list[str]:
    """Check a single metadata file.

    Returns
    -------
    A list of error messages, empty if the file is valid.
    """
    if not path.is_file():
        return [f"Missing metadata file `{path.name}`."]

    try:
        ProblemMetadata.from_yaml(path)
    except yaml.YAMLError as e:
        return [f"Invalid YAML: {e}"]
    except pydantic.ValidationError as e:
        return [
            f"{'/'.join(map(str, error['loc'])) or '<root>'}: {error['msg']}"
            for error in e.errors()
        ]

    return []


def main():
    """Check the metadata files of all problems."""
    num_failures = 0

    for problem_id in MODELS:
        errors = check_metadata_file(get_metadata_path(problem_id))

        print(problem_id)
        if errors:
            print("\n".join("\t" + error for error in errors))
            num_failures += 1
        print("=" * 100)  # just for output readability

    num_passed = len(MODELS) - num_failures
    print(f"Result: {Path(__file__).stem}")
    print(f"{num_passed} out of {len(MODELS)} passed.")
    print(f"{num_failures} out of {len(MODELS)} failed.")
    sys.exit(num_failures)
