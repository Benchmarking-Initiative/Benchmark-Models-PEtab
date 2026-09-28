"""Tests for the PEtab-looking-YAML detector."""

from benchmark_models_petab.check_petab_yaml import looks_like_petab_yaml


def test_petab_v1_yaml_is_detected(tmp_path):
    """A YAML file with the mandatory PEtab v1 top-level keys is detected."""
    yaml_file = tmp_path / "problem.yaml"
    yaml_file.write_text(
        "format_version: 1\n"
        "parameter_file: parameters.tsv\n"
        "problems:\n"
        "- condition_files:\n"
        "  - conditions.tsv\n"
    )

    assert looks_like_petab_yaml(yaml_file) is True


def test_petab_select_yaml_is_not_detected(tmp_path):
    """A petab_select YAML lacks the `problems` key and is not mistaken for
    a PEtab problem."""
    yaml_file = tmp_path / "petab_select_problem.yaml"
    yaml_file.write_text(
        "format_version: beta_1\ncriterion: BIC\nmethod: forward\n"
    )

    assert looks_like_petab_yaml(yaml_file) is False


def test_unrelated_yaml_is_not_detected(tmp_path):
    """An arbitrary YAML file without PEtab keys is not detected."""
    yaml_file = tmp_path / "config.yaml"
    yaml_file.write_text("some_key: some_value\n")

    assert looks_like_petab_yaml(yaml_file) is False


def test_non_mapping_yaml_is_not_detected(tmp_path):
    """A YAML file that doesn't parse to a mapping (e.g. a plain list) is
    not detected."""
    yaml_file = tmp_path / "list.yaml"
    yaml_file.write_text("- a\n- b\n")

    assert looks_like_petab_yaml(yaml_file) is False


def test_invalid_yaml_is_not_detected(tmp_path):
    """A file that isn't valid YAML is not detected, rather than raising."""
    yaml_file = tmp_path / "broken.yaml"
    yaml_file.write_text("key: [unclosed\n")

    assert looks_like_petab_yaml(yaml_file) is False
