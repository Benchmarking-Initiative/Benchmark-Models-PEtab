"""Version-independent per-problem metadata."""

import json
from importlib.resources import files
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

from ._ids import resolve_id
from .C import METADATA_FILENAME, MODELS_DIR

METADATA_SCHEMA_FILENAME = "metadata.schema.json"


class ProblemMetadata(BaseModel):
    """Version-independent metadata of a benchmark problem."""

    model_config = ConfigDict(
        extra="forbid",
        title="Benchmark problem metadata",
        json_schema_extra={
            "$schema": "https://json-schema.org/draft/2020-12/schema"
        },
    )

    short_description: str = Field(
        min_length=20,
        max_length=160,
        pattern=r"^[A-Z][\x20-\x7E]*\.$",
        description=(
            "Single-sentence summary of the problem: the type of model "
            "(e.g., biochemical reaction network, compartmental "
            "epidemiological model), the biological system, and, where "
            "informative, the data. Plain ASCII text, no line breaks, "
            "ending with a period."
        ),
    )

    @classmethod
    def from_yaml(cls, path: str | Path) -> "ProblemMetadata":
        """Load and validate a metadata file.

        Raises
        ------
        pydantic.ValidationError
            If the metadata is invalid.
        """
        with open(path, encoding="utf-8") as f:
            return cls.model_validate(yaml.safe_load(f))


def get_metadata_schema() -> dict[str, Any]:
    """Get the JSON schema for the per-problem metadata files."""
    return ProblemMetadata.model_json_schema()


def get_metadata_path(id_: str) -> Path:
    """Get the path to the metadata file of the given problem.

    Parameters
    ----------
    id_: Problem name, as in `benchmark_models_petab.MODELS`.

    Returns
    -------
    The path to the metadata file. The file is not guaranteed to exist.
    """
    return Path(MODELS_DIR, resolve_id(id_), METADATA_FILENAME)


def get_metadata(id_: str) -> ProblemMetadata:
    """Get the metadata of a benchmark problem.

    The metadata is not specific to a PEtab version.

    Parameters
    ----------
    id_: Problem name, as in `benchmark_models_petab.MODELS`.

    Returns
    -------
    The problem metadata.
    """
    path = get_metadata_path(id_)
    if not path.is_file():
        raise ValueError(f"Could not find metadata for problem `{id_}`.")
    return ProblemMetadata.from_yaml(path)


def write_metadata_schema(path: str | Path | None = None) -> None:
    """Write the JSON schema for the metadata files.

    By default, the packaged schema file is overwritten. Run after changing
    `ProblemMetadata`.
    """
    if path is None:
        path = Path(
            str(files(__package__) / "schemas" / METADATA_SCHEMA_FILENAME)
        )
    with open(path, "w", encoding="utf-8") as f:
        json.dump(get_metadata_schema(), f, indent=2)
        f.write("\n")
