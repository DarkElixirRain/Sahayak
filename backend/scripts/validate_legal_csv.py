"""Validate a legal knowledge CSV without importing anything.

Usage:
    python scripts/validate_legal_csv.py path/to/file.csv
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings  # noqa: E402
from app.services.csv_importer import CsvFormatError, validate_file  # noqa: E402


def _print_report(report) -> None:
    print("CSV validation completed.")
    print()
    print(f"File:  {report.file}")
    print(f"Rows:  {report.total}")
    print(f"Valid: {report.valid}")
    print(f"Invalid: {report.invalid}")
    print()

    for row_number in sorted(report.issues):
        print(f"Row {row_number}:")
        for issue in report.issues[row_number]:
            print(f"  - {issue.message} [{issue.field}]")

    if report.invalid == 0:
        print("All rows are valid.")


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print("Usage: python scripts/validate_legal_csv.py path/to/file.csv")
        return 2

    path = Path(argv[0])
    if not path.exists():
        print(f"File not found: {path}")
        return 2

    try:
        report = validate_file(path, database_url=settings.database_url)
    except CsvFormatError as exc:
        print(f"CSV could not be validated: {exc}")
        return 1

    _print_report(report)
    return 0 if report.invalid == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())