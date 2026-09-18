"""Convert a legacy Preeti-encoded Nepali CSV to Unicode (UTF-8, no BOM).

Reads a CSV produced with the pre-Unicode Preeti keyboard layout, converts the
indicated text columns to Unicode Devanagari, and writes a new CSV. The input
file is never modified. Conversion is deterministic and requires no network.

Usage:
    python scripts/convert_legacy_nepali.py INPUT.csv OUTPUT.csv
        [--columns part_title,chapter_title,section_title,section_text]
        [--stats]
        [--samples N]
        [--dev]           # also print a Devanagari coverage summary

Exit codes:
    0  conversion succeeded
    2  invalid arguments / unreadable input
    3  conversion finished but suspicious remnants were detected (with --stats)
"""

from __future__ import annotations

import argparse
import csv
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.legacy_preeti import (  # noqa: E402
    convert_text,
    devanagari_char_count,
    has_devanagari,
    legacy_remnants,
)

DEFAULT_TEXT_COLUMNS = (
    "part_title", "chapter_title", "section_title", "section_text",
)


def _read_rows(path: Path) -> list[dict[str, str]]:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        text = raw.decode("utf-8-sig")
    else:
        text = raw.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text), lineterminator="\n")
    if reader.fieldnames is None:
        raise ValueError(f"CSV has no header row: {path}")
    return [dict(row) for row in reader]


def _convert_rows(
    rows: list[dict[str, str]], columns: tuple[str, ...], fieldnames: list[str]
) -> list[dict[str, str]]:
    missing = [c for c in columns if c not in fieldnames]
    if missing:
        raise ValueError(f"Missing text columns in CSV: {', '.join(missing)}")
    converted: list[dict[str, str]] = []
    for row in rows:
        out = dict(row)
        for col in columns:
            out[col] = convert_text(row.get(col, ""))
        converted.append(out)
    return converted


def _print_stats(path: Path, rows: list[dict[str, str]], columns: tuple[str, ...]) -> int:
    total = len(rows)
    rows_dev = 0
    suspicious: list[str] = []
    total_chars = 0
    for row in rows:
        dev_chars = 0
        has_dev = False
        for col in columns:
            val = row.get(col, "")
            if has_devanagari(val):
                has_dev = True
            dev_chars += devanagari_char_count(val)
            rem = legacy_remnants(val)
            if rem:
                suspicious.append("".join(rem))
        if has_dev:
            rows_dev += 1
        total_chars += dev_chars

    print(f"Rows converted:            {total}")
    print(f"Rows containing Devanagari: {rows_dev}")
    print(f"Total Devanagari chars:     {total_chars}")
    if suspicious:
        distinct = sorted(set("".join(suspicious)))
        print(f"Suspicious legacy remnants: {len(suspicious)} row(s) -> {distinct!r}")
        return 3
    print("Suspicious legacy remnants: 0")
    return 0


def _print_samples(rows: list[dict[str, str]], columns: tuple[str, ...], n: int) -> None:
    shown = 0
    for row in rows:
        for col in columns:
            if shown >= n:
                return
            val = row.get(col, "")
            if not val.strip():
                continue
            shown += 1
            preview = val if len(val) <= 160 else val[:157] + "..."
            print(f"\n--- {col} (sample {shown}) ---")
            print(preview)
            print()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Convert legacy Preeti CSV to Unicode.")
    parser.add_argument("input", type=Path, help="input CSV (UTF-8 or UTF-8-BOM)")
    parser.add_argument("output", type=Path, help="output CSV (UTF-8, no BOM)")
    parser.add_argument(
        "--columns",
        default=",".join(DEFAULT_TEXT_COLUMNS),
        help="comma-separated text columns to convert (default: all four title/text columns)",
    )
    parser.add_argument("--stats", action="store_true", help="print conversion statistics")
    parser.add_argument("--samples", type=int, default=0, help="print N before/after samples")
    parser.add_argument("--dev", action="store_true", help="print Devanagari coverage summary")
    args = parser.parse_args(argv)

    if not args.input.exists():
        print(f"Input file not found: {args.input}", file=sys.stderr)
        return 2

    columns = tuple(c.strip() for c in args.columns.split(",") if c.strip())
    try:
        original = _read_rows(args.input)
    except (UnicodeDecodeError, ValueError) as exc:
        print(f"Cannot read input CSV: {exc}", file=sys.stderr)
        return 2

    fieldnames = list(original[0].keys()) if original else [c for c in columns]
    try:
        converted = _convert_rows(original, columns, fieldnames)
    except ValueError as exc:
        print(f"Conversion aborted: {exc}", file=sys.stderr)
        return 2

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(converted)

    print(f"Wrote {len(converted)} rows -> {args.output}")

    if args.samples:
        _print_samples(converted, columns, args.samples)
    if args.dev:
        print(f"DevTEXT columns: {', '.join(columns)}")
    if args.stats:
        code = _print_stats(args.output, converted, columns)
        return code
    return 0


if __name__ == "__main__":
    raise SystemExit(main())