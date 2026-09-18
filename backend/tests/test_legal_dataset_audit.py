"""Focused, database-free tests for the Phase 3B legal dataset audit."""

import csv
from pathlib import Path

from scripts.audit_legal_dataset import audit


DATA = Path(__file__).parents[1] / "data" / "legal"
ORIGINAL = DATA / "muluki_dewani_samhita_2074_structured.csv"
UNICODE = DATA / "muluki_dewani_samhita_2074_unicode.csv"
IMPORTER = DATA / "muluki_dewani_samhita_2074_importer_ready.csv"


def test_current_dataset_passes_critical_audit_without_database():
    result = audit(ORIGINAL, UNICODE, IMPORTER)
    assert result["critical_failure"] is False
    assert result["status"] == "PASS"
    assert result["rows"] == {"original": 721, "unicode": 721, "importer_ready": 721}
    assert result["hierarchy"] == {}
    assert result["text_preservation"]["mismatches"] == []
    assert result["importer_validation"]["invalid"] == 0


def test_headers_and_field_counts_are_exact():
    result = audit(ORIGINAL, UNICODE, IMPORTER)
    assert result["schema"] == {
        "structured_headers_ok": True,
        "importer_header_ok": True,
        "field_counts_ok": True,
    }
    assert not any(result["structural_errors"].values())


def test_unicode_quality_and_known_row_141_correction_are_reported():
    result = audit(ORIGINAL, UNICODE, IMPORTER)
    assert result["unicode"]["devanagari_characters"] == 372509
    assert result["unicode"]["rows_containing_devanagari"] == 721
    assert result["unicode"]["nfc_failures"] == 0
    assert result["unicode"]["suspicious"] == {
        "replacement_characters": 0,
        "control_characters": 0,
        "private_use_characters": 0,
        "mojibake_markers": 0,
    }
    assert result["unicode"]["legacy_remnants"] == []


def test_audit_does_not_modify_original_source():
    before = ORIGINAL.read_bytes()
    audit(ORIGINAL, UNICODE, IMPORTER)
    assert ORIGINAL.read_bytes() == before


def test_row_141_text_is_preserved_in_importer_ready():
    with UNICODE.open(encoding="utf-8", newline="") as source, IMPORTER.open(encoding="utf-8", newline="") as target:
        source_row = list(csv.DictReader(source))[140]
        importer_row = list(csv.DictReader(target))[140]
    assert source_row["section_no"] == "141"
    assert "mव्यति" not in source_row["section_text"]
    assert "व्यक्ति" in source_row["section_text"]
    assert importer_row["content"].endswith(source_row["section_text"])


def test_authorized_section_141_correction_is_scoped():
    unicode_text = UNICODE.read_text(encoding="utf-8")
    importer_text = IMPORTER.read_text(encoding="utf-8")
    assert unicode_text.count("mव्यति") == 0
    assert importer_text.count("mव्यति") == 0
    assert unicode_text.count("व्यक्ति") >= 1
    assert importer_text.count("व्यक्ति") >= 1


def test_synthetic_empty_required_field_is_critical(tmp_path):
    source = tmp_path / "source.csv"
    unicode_file = tmp_path / "unicode.csv"
    importer = tmp_path / "importer.csv"
    structured_header = "part_no,part_title,chapter_no,chapter_title,section_no,section_title,section_text\n"
    structured_row = "1,भाग,1,अध्याय,1,दफा,कानूनी पाठ\n"
    source.write_text(structured_header + structured_row, encoding="utf-8")
    unicode_file.write_text(structured_header + "1,,1,अध्याय,1,दफा,कानूनी पाठ\n", encoding="utf-8")
    importer.write_text(
        "domain,document_title,document_type,provision_number,provision_title,content,language,source_name,source_type,source_url,verified\n"
        "civil,कानून,act,1,दफा,भाग १ — \nपरिच्छेद १ — अध्याय\nदफा १ — दफा\n\nकानूनी पाठ,nepali,स्रोत,law_commission,https://example.com,false\n",
        encoding="utf-8",
    )
    result = audit(source, unicode_file, importer)
    assert result["critical_failure"] is True
    assert any(item["field"] == "part_title" for item in result["empty_fields"])