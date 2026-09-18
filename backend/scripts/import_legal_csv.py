"""Import a validated legal knowledge CSV into the database.

Usage:
    python scripts/import_legal_csv.py path/to/file.csv [--best-effort]

By default the import is aborted if any row fails validation. Pass
``--best-effort`` to import only the valid rows and report the rest. All
database work happens in a single transaction; a database failure rolls back
the entire import.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings  # noqa: E402
from app.services.csv_importer import (  # noqa: E402
    CsvFormatError,
    import_csv_file,
)


def _print_report(report) -> None:
    print("Sahayak Legal Knowledge Import")
    print()
    print(f"File:")
    print(f"{report.file}")
    print()
    print(f"Total rows:       {report.total}")
    print(f"Inserted:         {report.inserted}")
    print(f"Updated:          {report.updated}")
    print(f"Skipped:          {report.skipped}")
    print(f"Failed:           {report.failed}")
    print()
    print(f"Verified records: {report.verified}")
    print(f"Unverified:       {report.unverified}")
    print()

    for failure in report.failures:
        print(f"  - {failure}")


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0].startswith("-"):
        print("Usage: python scripts/import_legal_csv.py path/to/file.csv [--best-effort]")
        return 2

    path = Path(argv[0])
    best_effort = "--best-effort" in argv
    if not path.exists():
        print(f"File not found: {path}")
        return 2

    try:
        report = import_csv_file(
            path,
            best_effort=best_effort,
            database_url=settings.database_url,
        )
    except CsvFormatError as exc:
        print(f"CSV could not be imported: {exc}")
        return 1

    _print_report(report)
    return 0 if report.failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())