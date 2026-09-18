"""Reshape the converted Muluki Dewani Samhita 2074 CSV into the importer schema.

Processes the Unicode (converted) CSV and writes a CSV that satisfies the legal
knowledge importer contract (EXPECTED_HEADER / REQUIRED_FIELDS from
app.services.csv_importer). Nothing is imported; this script only writes files.

Provenance rules:
    * the document is modelled as ONE act: "मुलुकी देवानी संहिता, २०७४"
    * every row is one दफा (provision) whose number and title come verbatim from
      the source dataset
    * the Part -> Chapter -> Section hierarchy is preserved in ``content`` by
      prefixing each provision with its भाग/परिच्छेद/दफा headings
    * domain is assigned per Part (see DOMAIN_BY_PART below) — a reviewable
      mapping, not an invention
    * verified=false: these provisions have NOT yet been checked against the
      authoritative source, so they are imported as unverified content

Usage:
    python scripts/reshape_to_importer_schema.py \
        data/legal/muluki_dewani_samhita_2074_unicode.csv \
        data/legal/muluki_dewani_samhita_2074_importer_ready.csv
"""

from __future__ import annotations

import argparse
import csv
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.csv_importer import EXPECTED_HEADER  # noqa: E402

DOCUMENT_TITLE = "मुलुकी देवानी संहिता, २०७४"
DOCUMENT_TYPE = "act"
LANGUAGE = "nepali"
SOURCE_NAME = "नेपाल कानून आयोग (Nepal Law Commission)"
SOURCE_TYPE = "law_commission"
SOURCE_URL = "https://lawcommission.gov.np/content/13455/civil-code-2074"
VERIFIED = "false"

# Reviewable domain mapping keyed by Part number of the source dataset.
DOMAIN_BY_PART: dict[str, str] = {
    "1": "civil",
    "2": "civil",
    "3": "family",
    "4": "land_property",
    "5": "civil",
}

DEV_DIGITS = str.maketrans("0123456789", "०१२३४५६७८९")


def _dev_num(value: str) -> str:
    return str(value).translate(DEV_DIGITS)


def _make_content(row: dict[str, str]) -> str:
    """Rebuild the provision content preserving Part -> Chapter -> Section."""
    part_no = _dev_num(row["part_no"])
    chapter_no = _dev_num(row["chapter_no"])
    section_no = _dev_num(row["section_no"])
    headings = [
        f"भाग {part_no} — {row['part_title']}",
        f"परिच्छेद {chapter_no} — {row['chapter_title']}",
        f"दफा {section_no} — {row['section_title']}",
    ]
    return "\n".join(headings + [""] + [row["section_text"]])


def _read_rows(path: Path) -> list[dict[str, str]]:
    raw = path.read_bytes()
    text = raw.decode("utf-8-sig") if raw.startswith(b"\xef\xbb\xbf") else raw.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise ValueError(f"CSV has no header row: {path}")
    return [dict(row) for row in reader]


def reshape(input_path: Path, output_path: Path) -> int:
    rows = _read_rows(input_path)
    require = {"part_no", "part_title", "chapter_no", "chapter_title",
               "section_no", "section_title", "section_text"}
    missing = require - set(rows[0]) if rows else require
    if missing:
        raise ValueError(f"Missing columns in {input_path}: {', '.join(sorted(missing))}")

    out_rows: list[dict[str, str]] = []
    for row in rows:
        part_no = row["part_no"]
        domain = DOMAIN_BY_PART.get(part_no)
        if not domain:
            raise ValueError(f"Part number not covered by DOMAIN_BY_PART: {part_no!r}")
        out_rows.append({
            "domain": domain,
            "document_title": DOCUMENT_TITLE,
            "document_type": DOCUMENT_TYPE,
            "provision_number": row["section_no"],
            "provision_title": row["section_title"],
            "content": _make_content(row),
            "language": LANGUAGE,
            "source_name": SOURCE_NAME,
            "source_type": SOURCE_TYPE,
            "source_url": SOURCE_URL,
            "verified": VERIFIED,
        })

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=EXPECTED_HEADER, lineterminator="\n")
        writer.writeheader()
        writer.writerows(out_rows)
    return len(out_rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Reshape converted Civil Code CSV to importer schema.")
    parser.add_argument("input", type=Path, help="converted Unicode CSV (7 columns)")
    parser.add_argument("output", type=Path, help="importer-ready CSV (11 columns)")
    args = parser.parse_args(argv)

    if not args.input.exists():
        print(f"Input file not found: {args.input}", file=sys.stderr)
        return 2
    try:
        count = reshape(args.input, args.output)
    except (ValueError, UnicodeDecodeError) as exc:
        print(f"Reshape failed: {exc}", file=sys.stderr)
        return 2
    print(f"Reshaped {count} provisions -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())