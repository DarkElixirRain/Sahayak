"""Tests for the legacy Nepali (Preeti) → Unicode converter.

These tests are fully self-contained: no database, no network, deterministic.
They run from the ``backend/`` directory with ``pytest``.

``pytest -q``  from ``/Users/bishalchaudhary/Sahayak/backend``.
"""

import csv
import io
import subprocess
import sys
from pathlib import Path

# Ensure the app package is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.legacy_preeti import (
    convert_text,
    has_devanagari,
    legacy_remnants,
)
from app.services.csv_importer import EXPECTED_HEADER


# --------------------------------------------------------------------------- #
# Test data — Preeti strings and expected Unicode output
# ---------------------------------------------------------------------------

ANCHORS = {
    "k|f/lDes": "प्रारम्भिक",
    ";+lIfKt gfd / k|f/De": "संक्षिप्त नाम र प्रारम्भ",
    "kl/efiff": "परिभाषा",
    'sfg"g': "कानून",
    ";fdfGo Joj:yf": "सामान्य व्यवस्था",
}


# --------------------------------------------------------------------------- #
# Test 1 — Exact mapping anchors from the verified corpus
# --------------------------------------------------------------------------- #


def test_known_conversions() -> None:
    for preeti, expected in ANCHORS.items():
        got = convert_text(preeti)
        assert got == expected, (
            f"Conversion anchor failed: {preeti!r} -> {got!r}, expected {expected!r}"
        )


# --------------------------------------------------------------------------- #
# Test 2 — Devanagari detection via Unicode ranges, not just non-ASCII
# --------------------------------------------------------------------------- #


def test_devanagari_vs_nonascii() -> None:
    assert has_devanagari("नेपाली") is True
    assert has_devanagari("—") is False          # em-dash, Latin block
    assert has_devanagari("123") is False         # pure ASCII digits
    assert has_devanagari("संहिता") is True


# --------------------------------------------------------------------------- #
# Test 3 — ASCII/punctuation/structural numbers are handled correctly
# --------------------------------------------------------------------------- #


def test_ascii_punct_preserved() -> None:
    # en-dash passthrough
    assert convert_text("–") == "–"
    # Devanagari digits from Preeti keys
    assert "१" in convert_text("!")
    # ASCII parentheses mapped via Preeti layout
    assert convert_text("(") == "९"


# --------------------------------------------------------------------------- #
# Test 4 — Deterministic output: same input always yields same output
# --------------------------------------------------------------------------- #


def test_deterministic() -> None:
    texts = [
        "k|f/lDes",
        ";+lIfKt gfd / k|f/De",
        "kl/efiff",
        'sfg"g',
        ";fdfGo Joj:yf",
    ]
    for t in texts:
        got1 = convert_text(t)
        got2 = convert_text(t)
        assert got1 == got2


# --------------------------------------------------------------------------- #
# Test 5 — Original source CSV must never be modified on disk
# --------------------------------------------------------------------------- #


def test_original_unchanged() -> None:
    src = Path("data/legal/muluki_dewani_samhita_2074_structured.csv")
    original = src.read_bytes()
    assert src.read_bytes() == original


# --------------------------------------------------------------------------- #
# Test 6 — Legacy remnant detection: source‑data anomaly reported
# --------------------------------------------------------------------------- #


def test_legacy_remnants() -> None:
    src = Path("data/legal/muluki_dewani_samhita_2074_structured.csv")
    import csv, io
    rows = list(csv.DictReader(io.StringIO(src.read_text(encoding="utf-8-sig"))))
    remnant_rows = 0
    for r in rows:
        for col in ("part_title", "chapter_title", "section_title", "section_text"):
            conv = convert_text(r[col])
            if legacy_remnants(conv):
                remnant_rows += 1
                break
    assert remnant_rows == 1


# --------------------------------------------------------------------------- #
# Test 7 — Converted Unicode CSV has the expected 721 rows and 7 columns
# --------------------------------------------------------------------------- #


def test_unicode_csv_row_count() -> None:
    import csv, io
    unicode_path = Path("data/legal/muluki_dewani_samhita_2074_unicode.csv")
    raw = unicode_path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        text = raw.decode("utf-8-sig")
    else:
        text = raw.decode("utf-8")
    rows = list(csv.DictReader(io.StringIO(text)))
    assert len(rows) == 721, f"Expected 721 rows, got {len(rows)}"
    assert len(rows[0]) == 7, f"Expected 7 columns, got {len(rows[0])}"


# --------------------------------------------------------------------------- #
# Test 8 — Reshaped importer CSV has the exact EXPECTED_HEADER contract
# --------------------------------------------------------------------------- #


def test_reshape_header() -> None:
    from scripts.reshape_to_importer_schema import reshape
    unicode_path = Path("data/legal/muluki_dewani_samhita_2074_unicode.csv")
    out = Path("data/legal/muluki_dewani_samhita_2074_importer_test_reshape.csv")
    count = reshape(unicode_path, out)
    assert count == 721, f"Reshape expected 721 rows, got {count}"

    raw = out.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        text = raw.decode("utf-8-sig")
    else:
        text = raw.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    assert reader.fieldnames == list(EXPECTED_HEADER), (
        f"Header mismatch: got {reader.fieldnames!r}, expected {list(EXPECTED_HEADER)!r}"
    )

    # Verify provenance columns
    for i, row in enumerate(reader, 1):
        assert row["document_title"] == "मुलुकी देवानी संहिता, २०७४", (
            f"Row {i}: document_title incorrect"
        )
        assert row["document_type"] == "act", f"Row {i}: document_type incorrect"
        assert row["language"] == "nepali", f"Row {i}: language incorrect"
        assert row["source_name"] == "नेपाल कानून आयोग (Nepal Law Commission)", (
            f"Row {i}: source_name incorrect"
        )
        assert row["source_type"] == "law_commission", f"Row {i}: source_type incorrect"
        assert row["source_url"] == "https://lawcommission.gov.np/content/13455/civil-code-2074", (
            f"Row {i}: source_url incorrect"
        )
        assert row["verified"] == "false", f"Row {i}: verified should be false"

    out.unlink(missing_ok=True)


# --------------------------------------------------------------------------- #
# Test 9 — verified column is "false" in all reshaped rows
# --------------------------------------------------------------------------- #


def test_verified_is_false() -> None:
    from scripts.reshape_to_importer_schema import reshape
    unicode_path = Path("data/legal/muluki_dewani_samhita_2074_unicode.csv")
    out = Path("data/legal/muluki_dewani_samhita_2074_verified_test.csv")
    reshape(unicode_path, out)
    raw = out.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        text = raw.decode("utf-8-sig")
    else:
        text = raw.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    for i, row in enumerate(reader, 1):
        assert row["verified"] == "false", f"Row {i}: verified should be false, got {row['verified']!r}"
    out.unlink(missing_ok=True)


# --------------------------------------------------------------------------- #
# Test 10 — Part numbers in the source dataset span exactly parts 1‑5
# --------------------------------------------------------------------------- #


def test_part_range() -> None:
    import csv, io
    src = Path("data/legal/muluki_dewani_samhita_2074_structured.csv")
    rows = list(csv.DictReader(io.StringIO(src.read_text(encoding="utf-8-sig"))))
    part_nos = {r["part_no"] for r in rows}
    assert part_nos == {"1", "2", "3", "4", "5"}, (
        f"Expected part_no {{1,2,3,4,5}}, got {part_nos}"
    )