"""Tests for the TSV format checker."""

from benchmark_models_petab.check_tsv_format import check_tsv_file


def test_well_formed_file_passes(tmp_path):
    """A clean, consistent TSV file yields no errors."""
    tsv_file = tmp_path / "ok.tsv"
    tsv_file.write_bytes(b"a\tb\tc\n1\t2\t3\n4\t\t6\n")

    assert check_tsv_file(tsv_file) == []


def test_empty_file_passes(tmp_path):
    """An empty file is not flagged."""
    tsv_file = tmp_path / "empty.tsv"
    tsv_file.write_bytes(b"")

    assert check_tsv_file(tsv_file) == []


def test_missing_field_is_detected(tmp_path):
    """A row with fewer fields than the header is flagged."""
    tsv_file = tmp_path / "short_row.tsv"
    tsv_file.write_bytes(b"a\tb\tc\n1\t2\n")

    errors = check_tsv_file(tsv_file)

    assert len(errors) == 1
    assert "Line 2" in errors[0]
    assert "expected 3 fields" in errors[0]
    assert "got 2" in errors[0]


def test_extra_field_is_detected(tmp_path):
    """A row with more fields than the header is flagged."""
    tsv_file = tmp_path / "long_row.tsv"
    tsv_file.write_bytes(b"a\tb\n1\t2\t3\n")

    errors = check_tsv_file(tsv_file)

    assert len(errors) == 1
    assert "expected 2 fields" in errors[0]
    assert "got 3" in errors[0]


def test_trailing_tab_empty_last_field_is_not_flagged(tmp_path):
    """A trailing tab encoding an empty last field is valid, not
    whitespace to strip, and must not be flagged."""
    tsv_file = tmp_path / "trailing_tab.tsv"
    tsv_file.write_bytes(b"a\tb\n1\t\n")

    assert check_tsv_file(tsv_file) == []


def test_field_with_trailing_space_is_detected(tmp_path):
    """Stray trailing whitespace within a non-empty field is flagged."""
    tsv_file = tmp_path / "trailing_space.tsv"
    tsv_file.write_bytes(b"a\tb\n1\t2 \n")

    errors = check_tsv_file(tsv_file)

    assert len(errors) == 1
    assert "Line 2" in errors[0]
    assert "leading/trailing space" in errors[0]


def test_field_with_leading_space_is_detected(tmp_path):
    """Stray leading whitespace within a non-empty field is flagged."""
    tsv_file = tmp_path / "leading_space.tsv"
    tsv_file.write_bytes(b"a\tb\n1\t 2\n")

    errors = check_tsv_file(tsv_file)

    assert len(errors) == 1
    assert "leading/trailing space" in errors[0]


def test_whitespace_only_field_is_not_flagged(tmp_path):
    """A field consisting solely of whitespace may be an intentional
    blank placeholder (e.g. a suppressed visualization axis label) and
    must not be flagged."""
    tsv_file = tmp_path / "blank_placeholder.tsv"
    tsv_file.write_bytes(b"a\tb\n1\t \n")

    assert check_tsv_file(tsv_file) == []


def test_crlf_line_endings_are_detected(tmp_path):
    """A file using '\\r\\n' line endings throughout is flagged."""
    tsv_file = tmp_path / "crlf.tsv"
    tsv_file.write_bytes(b"a\tb\r\n1\t2\r\n")

    errors = check_tsv_file(tsv_file)

    assert len(errors) == 1
    assert "\\r\\n" in errors[0]
    assert "instead of" in errors[0]


def test_mixed_line_endings_are_detected(tmp_path):
    """A file mixing '\\n' and '\\r\\n' line endings is flagged."""
    tsv_file = tmp_path / "mixed.tsv"
    tsv_file.write_bytes(b"a\tb\n1\t2\r\n3\t4\n")

    errors = check_tsv_file(tsv_file)

    assert len(errors) == 1
    assert "Mixed line endings" in errors[0]


def test_missing_trailing_newline_is_detected(tmp_path):
    """A file that does not end with a newline is flagged."""
    tsv_file = tmp_path / "no_final_newline.tsv"
    tsv_file.write_bytes(b"a\tb\n1\t2")

    errors = check_tsv_file(tsv_file)

    assert len(errors) == 1
    assert "does not end with a newline" in errors[0]


def test_extra_trailing_newline_is_detected(tmp_path):
    """A file with more than one trailing newline is flagged."""
    tsv_file = tmp_path / "extra_final_newline.tsv"
    tsv_file.write_bytes(b"a\tb\n1\t2\n\n")

    errors = check_tsv_file(tsv_file)

    # the blank line also shows up as a (0-field) row, so both checks fire
    assert any("more than one trailing newline" in e for e in errors)


def test_multiple_issues_are_all_reported(tmp_path):
    """A file with several independent problems reports all of them."""
    tsv_file = tmp_path / "multiple_issues.tsv"
    tsv_file.write_bytes(b"a\tb\r\n1\t2 \n3\n")

    errors = check_tsv_file(tsv_file)

    assert len(errors) == 3
    assert any("Mixed line endings" in e for e in errors)
    assert any("leading/trailing space" in e for e in errors)
    assert any("expected 2 fields" in e and "got 1" in e for e in errors)
