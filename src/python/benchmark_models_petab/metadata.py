"""Version-independent per-problem metadata."""

import json
from functools import cache
from importlib.resources import files
from pathlib import Path
from typing import Any

import jsonschema
import yaml

from .C import METADATA_FILENAME, MODELS_DIR

METADATA_SCHEMA_FILENAME = "metadata.schema.json"


@cache
def get_metadata_schema() -> dict[str, Any]:
    """Get the JSON schema for the per-problem metadata files."""
    schema_file = files(__package__) / "schemas" / METADATA_SCHEMA_FILENAME
    return json.loads(schema_file.read_text(encoding="utf-8"))


def get_metadata_path(id_: str) -> Path:
    """Get the path to the metadata file of the given problem.

    Parameters
    ----------
    id_: Problem name, as in `benchmark_models_petab.MODELS`.

    Returns
    -------
    The path to the metadata file. The file is not guaranteed to exist.
    """
    return Path(MODELS_DIR, id_, METADATA_FILENAME)


def validate_metadata(metadata: Any) -> None:
    """Validate problem metadata against the metadata schema.

    Raises
    ------
    jsonschema.ValidationError
        If the metadata is invalid.
    """
    jsonschema.validate(metadata, get_metadata_schema())


def get_metadata(id_: str) -> dict[str, Any]:
    """Get the metadata of a benchmark problem.

    The metadata is not specific to a PEtab version.

    Parameters
    ----------
    id_: Problem name, as in `benchmark_models_petab.MODELS`.

    Returns
    -------
    The problem metadata, e.g. ``{"description": "..."}``.
    """
    path = get_metadata_path(id_)
    if not path.is_file():
        raise ValueError(f"Could not find metadata for problem `{id_}`.")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)
