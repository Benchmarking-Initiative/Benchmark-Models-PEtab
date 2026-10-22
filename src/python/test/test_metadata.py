"""Tests for the per-problem metadata files."""

import json
from importlib.resources import files

import pydantic
import pytest
import yaml

import benchmark_models_petab as models
from benchmark_models_petab.check_metadata import check_metadata_file
from benchmark_models_petab.metadata import (
    METADATA_SCHEMA_FILENAME,
    ProblemMetadata,
    get_metadata_path,
    get_metadata_schema,
)

DESCRIPTION = "Reaction network model of something."
BIBTEX = """\
@article{Doe_Journal2000,
  author = {Doe, Jane},
  title = {Something},
  doi = {10.1234/ABC.5},
}
"""
REFERENCE = {"doi": "10.1234/abc.5", "bibtex": BIBTEX}
VALID = {"short_description": DESCRIPTION, "references": [REFERENCE]}


def with_reference(**kwargs):
    """`VALID` with the given fields of the first reference replaced."""
    return VALID | {"references": [REFERENCE | kwargs]}


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
    assert metadata.references[0].doi == "10.1021/pr5006923"
    assert metadata.references[0].bibtex_key == "Boehm_JProteomeRes2014"

    with pytest.raises(ValueError):
        models.get_metadata("not a problem name")


def test_get_bibtex():
    bibtex = models.get_bibtex(["Boehm_JProteomeRes2014", "Bachmann_MSB2011"])
    assert bibtex.startswith("@article{Boehm_JProteomeRes2014,\n")
    assert "}\n\n@article{Bachmann_MSB2011,\n" in bibtex
    assert bibtex.endswith("}\n")

    assert models.get_bibtex().count("\n@") == len(models.MODELS) - 1


@pytest.mark.parametrize("problem_id", models.MODELS)
def test_all_problems_have_valid_metadata(problem_id):
    assert check_metadata_file(get_metadata_path(problem_id)) == []


@pytest.mark.parametrize(
    "metadata",
    [
        VALID,
        VALID | {"references": [REFERENCE, REFERENCE]},
    ],
)
def test_valid_metadata(metadata):
    ProblemMetadata.model_validate(metadata)


@pytest.mark.parametrize(
    "metadata",
    [
        {},
        {"short_description": DESCRIPTION},
        VALID | {"short_description": None},
        VALID | {"short_description": "Too short."},
        VALID | {"short_description": "Reaction network model of something"},
        VALID | {"short_description": "reaction network model of something."},
        VALID | {"short_description": "Reaction network model\nof something."},
        VALID
        | {"short_description": "Reaction network model of Ca²⁺ signaling."},
        VALID
        | {
            "short_description": "Reaction network model of " + 200 * "x" + "."
        },
        {"description": DESCRIPTION, "references": [REFERENCE]},
        VALID | {"unknown": 1},
        ["short_description"],
        VALID | {"references": []},
        VALID | {"references": [{"doi": "10.1234/abc.5"}]},
        with_reference(unknown=1),
        with_reference(doi="doi:10.1234/abc.5"),
        with_reference(doi="10.1234/other"),
        with_reference(
            bibtex=BIBTEX.replace("  doi = {10.1234/ABC.5},\n", "")
        ),
        with_reference(bibtex=BIBTEX + BIBTEX),
        with_reference(bibtex="doi = {10.1234/abc.5}"),
    ],
)
def test_invalid_metadata(metadata):
    with pytest.raises(pydantic.ValidationError):
        ProblemMetadata.model_validate(metadata)


def test_check_metadata_file(tmp_path):
    path = tmp_path / "Doe_Journal2000" / "metadata.yaml"
    path.parent.mkdir()
    assert check_metadata_file(path) == [
        "Missing metadata file `metadata.yaml`."
    ]

    path.write_text("short_description: [unclosed\n")
    assert check_metadata_file(path)[0].startswith("Invalid YAML")

    path.write_text(
        yaml.safe_dump(VALID | {"short_description": "Too short."})
    )
    (error,) = check_metadata_file(path)
    assert error.startswith("short_description: ")

    path.write_text(yaml.safe_dump(VALID))
    assert check_metadata_file(path) == []

    path = path.rename(tmp_path / "metadata.yaml")
    (error,) = check_metadata_file(path)
    assert "does not match the problem ID" in error
