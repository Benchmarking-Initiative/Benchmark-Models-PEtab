"""Tests for the per-problem metadata files."""

import json
from importlib.resources import files

import pydantic
import pytest

import benchmark_models_petab as models
from benchmark_models_petab.check_metadata import check_metadata_file
from benchmark_models_petab.metadata import (
    METADATA_SCHEMA_FILENAME,
    ProblemMetadata,
    get_metadata_path,
    get_metadata_schema,
)


def test_packaged_schema_is_up_to_date():
    """The packaged JSON schema matches `ProblemMetadata`."""
    schema_file = (
        files("benchmark_models_petab") / "schemas" / METADATA_SCHEMA_FILENAME
    )
    packaged_schema = json.loads(schema_file.read_text(encoding="utf-8"))
    assert packaged_schema == get_metadata_schema(), (
        "Outdated metadata schema. Regenerate with "
        "`benchmark_models_petab.metadata.write_metadata_schema()`."
    )


def test_get_metadata():
    metadata = models.get_metadata("Boehm_JProteomeRes2014")
    assert isinstance(metadata, ProblemMetadata)
    assert "STAT5" in metadata.short_description

    with pytest.raises(ValueError):
        models.get_metadata("not a problem name")


@pytest.mark.parametrize("problem_id", models.MODELS)
def test_all_problems_have_valid_metadata(problem_id):
    assert check_metadata_file(get_metadata_path(problem_id)) == []


@pytest.mark.parametrize(
    "metadata",
    [
        {"short_description": "Reaction network model of something."},
    ],
)
def test_valid_metadata(metadata):
    ProblemMetadata.model_validate(metadata)


@pytest.mark.parametrize(
    "metadata",
    [
        {},
        {"short_description": None},
        {"short_description": "Too short."},
        {"short_description": "Reaction network model of something"},
        {"short_description": "reaction network model of something."},
        {"short_description": "Reaction network model\nof something."},
        {"short_description": "Reaction network model of Ca²⁺ signaling."},
        {"short_description": "Reaction network model of " + 200 * "x" + "."},
        {"description": "Reaction network model of something."},
        {
            "short_description": "Reaction network model of something.",
            "unknown": 1,
        },
        ["short_description"],
    ],
)
def test_invalid_metadata(metadata):
    with pytest.raises(pydantic.ValidationError):
        ProblemMetadata.model_validate(metadata)


def test_check_metadata_file(tmp_path):
    path = tmp_path / "metadata.yaml"
    assert check_metadata_file(path) == [
        "Missing metadata file `metadata.yaml`."
    ]

    path.write_text("short_description: [unclosed\n")
    assert check_metadata_file(path)[0].startswith("Invalid YAML")

    path.write_text("short_description: Too short.\n")
    (error,) = check_metadata_file(path)
    assert error.startswith("short_description: ")

    path.write_text(
        "short_description: Reaction network model of something.\n"
    )
    assert check_metadata_file(path) == []
