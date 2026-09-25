"""Check that TSV files are well-formed and render correctly in GitHub's
file preview.

Checks, for every ``*.tsv`` file under the benchmark problem directories:

* every row has the same number of fields as the header
* line endings are consistent (no mix of ``\\n`` and ``\\r\\n``)
* no field has stray leading/trailing whitespace
* the file ends with exactly one trailing newline
"""

import csv
import io
import sys
from pathlib import Path

from .C import MODELS_DIR


def check_tsv_file(tsv_file: Path) -> list[str]:
    """Check a single TSV file for formatting issues.

    Parameters
    ----------
    tsv_file: Path to the TSV file to check.

    Returns
    -------
    A list of human-readable error messages. Empty if the file is fine.
    """
    errors = []

    raw = tsv_file.read_bytes()
    if not raw:
        return errors

    if b"\r\n" in raw and raw.replace(b"\r\n", b"").count(b"\n"):
        errors.append("Mixed line endings (both '\\r\\n' and '\\n').")
    elif b"\r\n" in raw:
        errors.append("Uses '\\r\\n' line endings instead of '\\n'.")

    if not raw.endswith(b"\n"):
        errors.append("File does not end with a newline.")
    elif raw.endswith(b"\n\n") or raw.endswith(b"\r\n\r\n"):
        errors.append("File ends with more than one trailing newline.")

    text = raw.decode("utf-8")
    # use csv.reader (like pandas.read_csv, which petab uses under the
    # hood) rather than a plain str.split("\t"), so quoted fields are
    # handled the same way the actual PEtab readers would handle them
    rows = list(csv.reader(io.StringIO(text), delimiter="\t"))

    if not rows:
        return errors

    num_fields = len(rows[0])
    for i, fields in enumerate(rows, start=1):
        # a trailing tab is a legitimate empty last field, not whitespace
        # to trim, so check individual fields for stray leading/trailing
        # spaces instead of checking the raw line; a field consisting
        # only of whitespace is left alone, as it may be an intentional
        # blank placeholder (e.g. for a visualization label)
        if any(field.strip() and field != field.strip() for field in fields):
            errors.append(f"Line {i}: field with leading/trailing space.")

        if i > 1 and len(fields) != num_fields:
            errors.append(
                f"Line {i}: expected {num_fields} fields "
                f"(as in the header), got {len(fields)}."
            )

    return errors


def main():
    """Check the format of all TSV files in the benchmark collection."""
    num_failures = 0
    tsv_files = sorted(Path(MODELS_DIR).rglob("*.tsv"))

    for tsv_file in tsv_files:
        errors = check_tsv_file(tsv_file)
        if errors:
            num_failures += 1
            print(tsv_file.relative_to(MODELS_DIR))
            for error in errors:
                print(f"\t{error}")

    num_passed = len(tsv_files) - num_failures
    print("=" * 100)
    print(f"Result: {Path(__file__).stem}")
    print(f"{num_passed} out of {len(tsv_files)} passed.")
    print(f"{num_failures} out of {len(tsv_files)} failed.")
    # Fail unless all files passed
    sys.exit(1 if num_failures else 0)
