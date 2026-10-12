"""Tests for the per-problem metadata files."""

import jsonschema
import pytest

import benchmark_models_petab as models
from benchmark_models_petab.check_metadata import check_metadata_file
from benchmark_models_petab.metadata import (
    get_metadata_path,
    get_metadata_schema,
    validate_metadata,
)


def test_schema_is_valid():
    """The packaged schema can be loaded and is a valid JSON schema."""
    schema = get_metadata_schema()
    jsonschema.Draft202012Validator.check_schema(schema)
    assert "description" in schema["required"]


def test_get_metadata():
    metadata = models.get_metadata("Boehm_JProteomeRes2014")
    assert "STAT5" in metadata["description"]

    with pytest.raises(ValueError):
        models.get_metadata("not a problem name")


@pytest.mark.parametrize("problem_id", models.MODELS)
def test_all_problems_have_valid_metadata(problem_id):
    assert check_metadata_file(get_metadata_path(problem_id)) == []


@pytest.mark.parametrize(
    "metadata",
    [
        {"description": "Reaction network model of something."},
    ],
)
def test_valid_metadata(metadata):
    validate_metadata(metadata)


@pytest.mark.parametrize(
    "metadata",
    [
        {},
        {"description": None},
        {"description": "Too short."},
        {"description": "Reaction network model of something"},
        {"description": "reaction network model of something."},
        {"description": "Reaction network model\nof something."},
        {"description": "Reaction network model of Ca²⁺ signaling."},
        {"description": "Reaction network model of " + 200 * "x" + "."},
        {
            "description": "Reaction network model of something.",
            "unknown": 1,
        },
        ["description"],
    ],
)
def test_invalid_metadata(metadata):
    with pytest.raises(jsonschema.ValidationError):
        validate_metadata(metadata)


def test_check_metadata_file(tmp_path):
    path = tmp_path / "metadata.yaml"
    assert check_metadata_file(path) == [
        "Missing metadata file `metadata.yaml`."
    ]

    path.write_text("description: [unclosed\n")
    assert check_metadata_file(path)[0].startswith("Invalid YAML")

    path.write_text("description: Too short.\n")
    (error,) = check_metadata_file(path)
    assert error.startswith("description: ")

    path.write_text("description: Reaction network model of something.\n")
    assert check_metadata_file(path) == []
