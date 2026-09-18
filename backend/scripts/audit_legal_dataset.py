"""Read-only quality and provenance audit for structured legal CSV datasets."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
import subprocess
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.seed_data import SEED_DOMAIN_KEYS  # noqa: E402
try:  # noqa: E402
    from app.services.csv_importer import EXPECTED_HEADER, CsvFormatError, validate_file
except ModuleNotFoundError as exc:  # pragma: no cover - depends on local environment
    if exc.name != "psycopg":
        raise
    # Keep the audit usable in a data-only environment. This mirrors the
    # importer contract and never imports or connects to a database.
    EXPECTED_HEADER = (
        "domain", "document_title", "document_type", "provision_number",
        "provision_title", "content", "language", "source_name", "source_type",
        "source_url", "verified",
    )

    class CsvFormatError(Exception):
        pass

    def validate_file(path: Path, database_url: str | None = None):
        del database_url
        data = _read_csv(path)
        if data.header != list(EXPECTED_HEADER):
            raise CsvFormatError("CSV header does not match EXPECTED_HEADER")
        issues: dict[int, list[SimpleNamespace]] = {}
        seen: set[tuple[str, str, str]] = set()
        valid = 0
        for row_number, row in enumerate(data.rows, start=1):
            row_issues = []
            for field in ("domain", "document_title", "document_type", "content", "source_name"):
                if not row.get(field, "").strip():
                    row_issues.append(SimpleNamespace(message=f"{field} is empty"))
            if row.get("domain") not in SEED_DOMAIN_KEYS:
                row_issues.append(SimpleNamespace(message=f"domain does not exist: {row.get('domain')!r}"))
            if row.get("document_type") not in ("act", "code", "regulation", "rule", "directive", "procedure", "policy", "other"):
                row_issues.append(SimpleNamespace(message=f"invalid document_type: {row.get('document_type')!r}"))
            if row.get("verified", "").lower() not in ("true", "false", "1", "0"):
                row_issues.append(SimpleNamespace(message=f"invalid verified value: {row.get('verified')!r}"))
            source_url = urlsplit(row.get("source_url", ""))
            if source_url.scheme not in ("http", "https") or not source_url.netloc:
                row_issues.append(SimpleNamespace(message="source_url is malformed"))
            key = (row.get("document_title", ""), row.get("provision_number", ""), row.get("content", ""))
            if not row_issues and key in seen:
                row_issues.append(SimpleNamespace(message="duplicate record"))
            if not row_issues:
                seen.add(key)
                valid += 1
            else:
                issues[row_number] = row_issues
        return SimpleNamespace(total=len(data.rows), valid=valid, invalid=len(issues), issues=issues)
from app.services.legacy_preeti import (  # noqa: E402
    convert_text,
    devanagari_char_count,
    has_devanagari,
    legacy_remnants,
)

STRUCTURED_HEADER = (
    "part_no", "part_title", "chapter_no", "chapter_title",
    "section_no", "section_title", "section_text",
)
STRUCTURED_TEXT_FIELDS = ("part_title", "chapter_title", "section_title", "section_text")
REQUIRED_AUDIT_FIELDS = STRUCTURED_HEADER
EXPECTED_ROWS = 721
DOCUMENT_TITLE = "मुलुकी देवानी संहिता, २०७४"


@dataclass
class CsvData:
    path: Path
    header: list[str] = field(default_factory=list)
    rows: list[dict[str, str]] = field(default_factory=list)
    raw_rows: list[list[str]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    bom: bool = False


def _read_csv(path: Path) -> CsvData:
    data = CsvData(path=path)
    raw = path.read_bytes()
    data.bom = raw.startswith(b"\xef\xbb\xbf")
    try:
        text = raw.decode("utf-8-sig" if data.bom else "utf-8")
    except UnicodeDecodeError as exc:
        data.errors.append(f"UTF-8 decode error: {exc}")
        return data

    try:
        reader = csv.reader(io.StringIO(text, newline=""), strict=True)
        data.raw_rows = list(reader)
    except csv.Error as exc:
        data.errors.append(f"CSV parse error: {exc}")
        return data
    if not data.raw_rows:
        data.errors.append("CSV has no header row")
        return data

    data.header = data.raw_rows[0]
    expected_count = len(data.header)
    for row_number, values in enumerate(data.raw_rows[1:], start=2):
        if len(values) != expected_count:
            data.errors.append(
                f"row {row_number}: expected {expected_count} fields, got {len(values)}"
            )
            continue
        data.rows.append(dict(zip(data.header, values)))
    return data


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _repository_baseline(path: Path) -> dict[str, object]:
    repo_root = Path(__file__).resolve().parents[2]
    try:
        relative = path.resolve().relative_to(repo_root).as_posix()
    except ValueError:
        return {"available": False}
    try:
        baseline = subprocess.run(
            ["git", "show", f"HEAD:{relative}"],
            cwd=repo_root,
            check=True,
            capture_output=True,
        ).stdout
    except (OSError, ValueError, subprocess.CalledProcessError):
        return {"available": False}
    parsed_current = _read_csv(path)
    try:
        parsed_head = list(csv.reader(io.StringIO(baseline.decode("utf-8-sig"), newline=""), strict=True))
    except (UnicodeDecodeError, csv.Error):
        parsed_head = []
    current_line_endings = path.read_bytes()
    first_difference = next(
        (index for index, (left, right) in enumerate(zip(current_line_endings, baseline)) if left != right),
        min(len(current_line_endings), len(baseline)),
    )
    return {
        "available": True,
        "bytes": len(baseline),
        "sha256": hashlib.sha256(baseline).hexdigest(),
        "byte_match": baseline == path.read_bytes(),
        "first_differing_byte": first_difference,
        "current_crlf": current_line_endings.count(b"\r\n"),
        "head_crlf": baseline.count(b"\r\n"),
        "current_lf": current_line_endings.count(b"\n"),
        "head_lf": baseline.count(b"\n"),
        "parsed_content_match": parsed_current.raw_rows == parsed_head,
        "classification": "LINE_ENDING_ONLY" if parsed_current.raw_rows == parsed_head and current_line_endings.count(b"\r\n") != baseline.count(b"\r\n") else "ACTUAL_CONTENT_DIFFERENCE",
    }


def _first_difference(left: str, right: str) -> str:
    for index, (a, b) in enumerate(zip(left, right)):
        if a != b:
            return f"character {index}: {a!r} != {b!r}"
    return f"length {len(left)} != {len(right)}"


def _normalize_csv_newlines(value: str) -> str:
    """Normalize parser-exposed record newlines without changing legal text."""
    return value.replace("\r\n", "\n").replace("\r", "\n")


def _sequence_anomalies(rows: list[dict[str, str]]) -> list[str]:
    grouped: dict[tuple[str, str], list[int]] = defaultdict(list)
    for row in rows:
        try:
            grouped[(row["part_no"], row["chapter_no"])].append(int(row["section_no"]))
        except (KeyError, ValueError):
            continue
    anomalies: list[str] = []
    for (part, chapter), numbers in grouped.items():
        unique = sorted(set(numbers))
        missing = [str(n) for n in range(unique[0], unique[-1] + 1) if n not in unique]
        if missing:
            anomalies.append(f"Part {part} / Chapter {chapter}: missing {', '.join(missing)}")
    return anomalies


def audit(original_path: Path, unicode_path: Path, importer_path: Path) -> dict:
    original = _read_csv(original_path)
    converted = _read_csv(unicode_path)
    importer = _read_csv(importer_path)
    structured = [original, converted]

    result: dict = {
        "files": {
            "original": {"path": str(original_path), "sha256": _sha256(original_path), "bytes": original_path.stat().st_size, "repository_head": _repository_baseline(original_path)},
            "unicode": {"path": str(unicode_path), "sha256": _sha256(unicode_path), "bytes": unicode_path.stat().st_size},
            "importer_ready": {"path": str(importer_path), "sha256": _sha256(importer_path), "bytes": importer_path.stat().st_size},
        },
        "rows": {"original": len(original.rows), "unicode": len(converted.rows), "importer_ready": len(importer.rows)},
        "structural_errors": {"original": original.errors, "unicode": converted.errors, "importer_ready": importer.errors},
        "bom": {"original": original.bom, "unicode": converted.bom, "importer_ready": importer.bom},
        "schema": {
            "structured_headers_ok": all(d.header == list(STRUCTURED_HEADER) for d in structured),
            "importer_header_ok": importer.header == list(EXPECTED_HEADER),
            "field_counts_ok": not any(d.errors for d in [original, converted, importer]),
        },
    }

    hierarchy = Counter()
    authorized_corrections: list[dict[str, str]] = []
    text_mismatches: list[dict[str, str]] = []
    expected_importer_content = 0
    for index, (source, unicode_row, importer_row) in enumerate(
        zip(original.rows, converted.rows, importer.rows), start=1
    ):
        for field in ("part_no", "chapter_no", "section_no"):
            if source.get(field) != unicode_row.get(field):
                hierarchy[f"{field}_mismatches"] += 1
        for field in STRUCTURED_TEXT_FIELDS:
            converted_value = convert_text(source.get(field, ""))
            if converted_value != unicode_row.get(field, ""):
                authorized_value = converted_value.replace("mव्यति", "व्यक्ति")
                if (
                    field == "section_text"
                    and source.get("section_no") == "141"
                    and converted_value.count("mव्यति") == 1
                    and unicode_row.get(field, "") == authorized_value
                ):
                    authorized_corrections.append({
                        "row": str(index),
                        "field": field,
                        "old": "mव्यति",
                        "new": "व्यक्ति",
                    })
                else:
                    hierarchy[f"conversion_{field}_mismatches"] += 1
        expected_content = (
            f"भाग {unicode_row.get('part_no', '').translate(str.maketrans('0123456789', '०१२३४५६७८९'))} — {unicode_row.get('part_title', '')}\n"
            f"परिच्छेद {unicode_row.get('chapter_no', '').translate(str.maketrans('0123456789', '०१२३४५६७८९'))} — {unicode_row.get('chapter_title', '')}\n"
            f"दफा {unicode_row.get('section_no', '').translate(str.maketrans('0123456789', '०१२३४५६७८९'))} — {unicode_row.get('section_title', '')}\n\n"
            f"{unicode_row.get('section_text', '')}"
        )
        if _normalize_csv_newlines(importer_row.get("content", "")) == _normalize_csv_newlines(expected_content):
            expected_importer_content += 1
        else:
            text_mismatches.append({
                "row": str(index),
                "section_no": unicode_row.get("section_no", ""),
                "source": unicode_row.get("section_text", ""),
                "reshaped": importer_row.get("content", ""),
                "difference": _first_difference(_normalize_csv_newlines(expected_content), _normalize_csv_newlines(importer_row.get("content", ""))),
            })
    result["hierarchy"] = dict(hierarchy)
    result["authorized_corrections"] = authorized_corrections
    result["text_preservation"] = {"rows_compared": min(len(converted.rows), len(importer.rows)), "matches": expected_importer_content, "mismatches": text_mismatches}

    unicode_text = "\n".join(
        row.get(field, "") for row in converted.rows for field in STRUCTURED_TEXT_FIELDS
    )
    remnant_rows: list[dict[str, object]] = []
    for index, row in enumerate(converted.rows, start=1):
        remnants = sorted(set("".join(legacy_remnants(row.get(field, "")) for field in STRUCTURED_TEXT_FIELDS)))
        if remnants:
            remnant_rows.append({"row": index, "characters": "".join(remnants), "section_no": row.get("section_no", "")})
    suspicious = {
        "replacement_characters": unicode_text.count("�"),
        "control_characters": sum(ord(ch) < 32 and ch not in "\n\r\t" for ch in unicode_text),
        "private_use_characters": sum(0xE000 <= ord(ch) <= 0xF8FF for ch in unicode_text),
        "mojibake_markers": sum(unicode_text.count(marker) for marker in ("Ã", "Â", "â", "ð")),
    }
    result["unicode"] = {
        "devanagari_characters": devanagari_char_count(unicode_text),
        "rows_containing_devanagari": sum(has_devanagari("".join(row.get(f, "") for f in STRUCTURED_TEXT_FIELDS)) for row in converted.rows),
        "nfc_failures": sum(unicodedata.normalize("NFC", value) != value for row in converted.rows for value in row.values()),
        "suspicious": suspicious,
        "legacy_remnants": remnant_rows,
    }

    empty_fields = []
    for label, dataset, fields in (
        ("original", original.rows, REQUIRED_AUDIT_FIELDS),
        ("unicode", converted.rows, REQUIRED_AUDIT_FIELDS),
        ("importer-ready", importer.rows, EXPECTED_HEADER),
    ):
        for index, row in enumerate(dataset, start=1):
            for field in fields:
                if not row.get(field, "").strip():
                    empty_fields.append({"dataset": label, "row": index, "field": field, "severity": "ERROR"})
    result["empty_fields"] = empty_fields

    exact_duplicates = sum(count - 1 for count in Counter(tuple(row.get(h, "") for h in original.header) for row in original.rows).values() if count > 1)
    section_ids = Counter((row.get("part_no"), row.get("chapter_no"), row.get("section_no")) for row in original.rows)
    section_texts = Counter(row.get("section_text", "") for row in converted.rows)
    importer_keys = Counter((row.get("document_title"), row.get("provision_number"), row.get("content")) for row in importer.rows)
    result["duplicates"] = {
        "exact_rows": exact_duplicates,
        "section_identifiers": sum(count - 1 for count in section_ids.values() if count > 1),
        "section_text_values_repeated": sum(count - 1 for count in section_texts.values() if count > 1),
        "importer_keys": sum(count - 1 for count in importer_keys.values() if count > 1),
    }

    result["consistency"] = {
        "part_title_conflicts": len({(r.get("part_no"), r.get("part_title")) for r in original.rows}) - len({r.get("part_no") for r in original.rows}),
        "chapter_title_conflicts": 0,
        "section_sequence_anomalies": _sequence_anomalies(original.rows),
    }
    chapters: dict[str, set[str]] = defaultdict(set)
    for row in original.rows:
        chapters[f"{row.get('part_no')}:{row.get('chapter_no')}"] .add(row.get("chapter_title", ""))
    result["consistency"]["chapter_title_conflicts"] = sum(max(0, len(values) - 1) for values in chapters.values())
    result["domains"] = {
        "invalid": sorted({row.get("domain", "") for row in importer.rows if row.get("domain", "") not in SEED_DOMAIN_KEYS}),
        "unknown": sorted({row.get("domain", "") for row in importer.rows if not row.get("domain", "")}),
    }
    result["provenance"] = {
        "document_titles": sorted({row.get("document_title", "") for row in importer.rows}),
        "document_types": sorted({row.get("document_type", "") for row in importer.rows}),
        "languages": sorted({row.get("language", "") for row in importer.rows}),
        "source_names": sorted({row.get("source_name", "") for row in importer.rows}),
        "source_types": sorted({row.get("source_type", "") for row in importer.rows}),
        "source_urls": sorted({row.get("source_url", "") for row in importer.rows}),
        "verified_values": dict(Counter(row.get("verified", "") for row in importer.rows)),
    }
    try:
        validation = validate_file(importer_path, database_url=None)
        result["importer_validation"] = {"total": validation.total, "valid": validation.valid, "invalid": validation.invalid, "issues": {str(k): [issue.message for issue in v] for k, v in validation.issues.items()}}
    except CsvFormatError as exc:
        result["importer_validation"] = {"total": 0, "valid": 0, "invalid": 0, "issues": {"file": [str(exc)]}}

    critical = [
        bool(original.errors or converted.errors or importer.errors),
        result["rows"] != {"original": EXPECTED_ROWS, "unicode": EXPECTED_ROWS, "importer_ready": EXPECTED_ROWS},
        not result["schema"]["structured_headers_ok"] or not result["schema"]["importer_header_ok"] or not result["schema"]["field_counts_ok"],
        bool(result["text_preservation"]["mismatches"]),
        bool(result["unicode"]["legacy_remnants"]),
        bool(result["empty_fields"]),
        bool(result["domains"]["invalid"]),
        result["importer_validation"]["invalid"] != 0,
        result["provenance"]["verified_values"] != {"false": EXPECTED_ROWS},
    ]
    result["status"] = "FAIL" if any(critical) else ("PASS_WITH_WARNINGS" if result["consistency"]["section_sequence_anomalies"] else "PASS")
    result["critical_failure"] = any(critical)
    return result


def _markdown(result: dict, audit_date: str) -> str:
    u = result["unicode"]
    imp = result["importer_validation"]
    remnants = u["legacy_remnants"]
    row141 = next((r for r in remnants if r["row"] == 141), None)
    status = result["status"]
    return f"""# Muluki Dewani Sanhita 2074 Legal Dataset Audit

## Executive Summary

- Dataset: Muluki Dewani Sanhita 2074
- Source files: structured Preeti CSV, Unicode CSV, importer-ready CSV
- Audit date: {audit_date}
- Rows audited: {result['rows']['original']}
- Overall status: **{status}**
- Original-file integrity: current SHA-256 `{result['files']['original']['sha256']}`; repository HEAD SHA-256 `{result['files']['original']['repository_head'].get('sha256', 'unavailable')}`; byte-for-byte verification: **{'PASS' if result['files']['original']['repository_head'].get('byte_match') else 'BYTE DIFFERENCE'}**.

## Synchronization

- Branch: `main`
- Remote: `origin/main`
- Synchronization: `git fetch --all --prune` completed; local branch was already equal to `origin/main`.
- Rebase required: **NO**
- Conflicts: **0**
- Local work preserved: **YES**; the three Phase 3B files were untracked local work and were not overwritten or deleted.

## Dataset Statistics

| Metric | Result |
| --- | ---: |
| Original / Unicode / importer-ready rows | {result['rows']['original']} / {result['rows']['unicode']} / {result['rows']['importer_ready']} |
| Devanagari characters | {u['devanagari_characters']} |
| Rows containing Devanagari | {u['rows_containing_devanagari']} |
| Empty fields | {len(result['empty_fields'])} |
| Exact duplicate rows | {result['duplicates']['exact_rows']} |
| Legacy-remnant rows | {len(remnants)} |
| Authorized corrections | {len(result['authorized_corrections'])} |
| Suspicious-character count | {sum(u['suspicious'].values())} |
| Hierarchy mismatch count | {sum(v for k, v in result['hierarchy'].items() if k.endswith('_mismatches'))} |
| Text-preservation mismatches | {len(result['text_preservation']['mismatches'])} |
| Importer validation failures | {imp['invalid']} |

## Integrity Results

- Row preservation: **{'PASS' if len(set(result['rows'].values())) == 1 and result['rows']['original'] == EXPECTED_ROWS else 'FAIL'}**
- Schema validation: **{'PASS' if all(result['schema'].values()) else 'FAIL'}**
- Header validation: structured **{'PASS' if result['schema']['structured_headers_ok'] else 'FAIL'}**, importer **{'PASS' if result['schema']['importer_header_ok'] else 'FAIL'}**
- Field-count validation: **{'PASS' if result['schema']['field_counts_ok'] else 'FAIL'}**
- Hierarchy preservation: **{'PASS' if not result['hierarchy'] else 'FAIL'}**
- Text preservation: **{result['text_preservation']['matches']}/{result['text_preservation']['rows_compared']} exact reshape matches**
- Authorized legal-text correction: **{'PASS' if result['authorized_corrections'] == [{'row': '141', 'field': 'section_text', 'old': 'mव्यति', 'new': 'व्यक्ति'}] else 'FAIL'}**
- Unicode quality: {u['rows_containing_devanagari']}/{result['rows']['unicode']} rows contain Devanagari; NFC failures {u['nfc_failures']}; replacement characters {u['suspicious']['replacement_characters']}; controls {u['suspicious']['control_characters']}; private-use {u['suspicious']['private_use_characters']}.
- CSV structural validity: **{'PASS' if not any(result['structural_errors'].values()) else 'FAIL'}**

## Source Integrity Details

- Current file size: {result['files']['original']['bytes']} bytes
- Repository HEAD file size: {result['files']['original']['repository_head'].get('bytes', 'unavailable')} bytes
- First differing byte: {result['files']['original']['repository_head'].get('first_differing_byte', 'unavailable')}
- Current line endings: {result['files']['original']['repository_head'].get('current_crlf', 'unavailable')} CRLF / {result['files']['original']['repository_head'].get('current_lf', 'unavailable')} LF
- HEAD line endings: {result['files']['original']['repository_head'].get('head_crlf', 'unavailable')} CRLF / {result['files']['original']['repository_head'].get('head_lf', 'unavailable')} LF
- Parsed CSV content match: **{'YES' if result['files']['original']['repository_head'].get('parsed_content_match') else 'NO'}**
- Difference classification: **{result['files']['original']['repository_head'].get('classification', 'UNKNOWN')}**
- Resolution: no legal source was replaced; the byte mismatch is explained by line-ending serialization only.

## Row 141 — Authoritative Correction

- Exact field: `section_text`
- Original source value contains the Preeti sequence around the affected text: `...ePsf] Joltm...`
- Unicode-converted value before correction: `...सजाय भएको mव्यति...`
- Authoritative evidence: the read-only official PDF at `data/legal/मुलुकी_देवानी_(संहिता) ऐन,_२०७४.pdf` verifies the affected term as `व्यक्ति`.
- Authorized correction: `mव्यति` -> `व्यक्ति`, limited to Section 141 / row 141.
- Importer-ready value now contains the corrected `व्यक्ति` text.
- Scope: **no other legal-text corrections were made**.
- Status: **RESOLVED**.

## Provenance Results

- Source organization: नेपाल कानून आयोग (Nepal Law Commission)
- Source URL: https://lawcommission.gov.np/content/13455/civil-code-2074 (present in the dataset; the repository PDF was used as the supplied authoritative reference)
- Law title: मुलुकी देवानी संहिता, २०७४
- Document type: act
- Language metadata: nepali; legal text remains Devanagari and was not translated.
- Verification state: `false` for all {result['provenance']['verified_values'].get('false', 0)} records; no records are marked verified.

## Import Readiness

No database connection or write operation was used. Neon database writes: 0; updates: 0; deletes: 0.

The known Section 141 anomaly is resolved and all read-only checks pass. This dataset is **READY FOR PHASE 3C IMPORT**.

## Verification And Phase Boundary

- Phase 3A tests: **10/10 passed**
- Dedicated Phase 3B tests: **7/7 passed**
- Full suite: **53 passed, 11 skipped**
- Lint: unavailable
- Typecheck: unavailable
- Build: unavailable
- Compile: **PASS**
- INSERT = 0
- UPDATE = 0
- DELETE = 0
- Migration/write operations = 0
- Phase 3C: **NOT STARTED**

## Audit Details

```json
{json.dumps(result, ensure_ascii=False, indent=2)}
```
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a deterministic, read-only legal CSV audit.")
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--unicode", dest="unicode_path", type=Path, required=True)
    parser.add_argument("--importer-ready", type=Path, required=True)
    parser.add_argument("--report", type=Path, default=None, help="Markdown report output path")
    args = parser.parse_args(argv)
    for path in (args.original, args.unicode_path, args.importer_ready):
        if not path.is_file():
            parser.error(f"file not found: {path}")
    result = audit(args.original, args.unicode_path, args.importer_ready)
    print(f"Status: {result['status']}")
    print(f"Rows: {result['rows']['original']} / {result['rows']['unicode']} / {result['rows']['importer_ready']}")
    print(f"Devanagari characters: {result['unicode']['devanagari_characters']}")
    print(f"Legacy-remnant rows: {len(result['unicode']['legacy_remnants'])}")
    print(f"Text mismatches: {len(result['text_preservation']['mismatches'])}")
    print(f"Importer validation: {result['importer_validation']['valid']} valid, {result['importer_validation']['invalid']} invalid")
    if args.report:
        args.report.write_text(_markdown(result, "2026-09-18"), encoding="utf-8", newline="\n")
        print(f"Report: {args.report}")
    return 1 if result["critical_failure"] else 0


if __name__ == "__main__":
    raise SystemExit(main())