"""Unit tests for CSV validation and parsing (no database required)."""

import csv

import pytest

from app.services.csv_importer import (
    CsvFormatError,
    parse_verified,
    read_rows,
    to_row,
    validate_file,
    validate_row,
)

VALID_ROW = {
    "domain": "consumer",
    "document_title": "Consumer Protection Act",
    "document_type": "act",
    "provision_number": "1",
    "provision_title": "Short Title",
    "content": "A reasonably long consumer protection text for validation.",
    "language": "nepali",
    "source_name": "Nepal Law Commission",
    "source_type": "law_commission",
    "source_url": "https://lawcommission.gov.np/consumer-protection",
    "verified": "true",
}

SEED_KEYS = {"consumer", "family", "land_property", "civil"}


def write_csv(tmp_path, rows, encoding="utf-8"):
    path = tmp_path / "test.csv"
    header = list(rows[0].keys())
    with open(path, "w", encoding=encoding, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)
    return path


def issues_for(row, keys=None):
    return validate_row(row, 1, keys or SEED_KEYS, {})


# --------------------------------------------------------------------------- #
# parse_verified
# --------------------------------------------------------------------------- #

def test_parse_verified_accepts_booleans():
    assert parse_verified("true") is True
    assert parse_verified("TRUE") is True
    assert parse_verified("1") is True
    assert parse_verified("false") is False
    assert parse_verified("False") is False
    assert parse_verified("0") is False


def test_parse_verified_rejects_other_values():
    assert parse_verified("yes") is None
    assert parse_verified("") is None
    assert parse_verified("Maybe") is None


# --------------------------------------------------------------------------- #
# field validation
# --------------------------------------------------------------------------- #

def test_valid_row_has_no_issues():
    assert issues_for(dict(VALID_ROW)) == []


@pytest.mark.parametrize(
    "field",
    ["domain", "document_title", "document_type", "content", "source_name"],
)
def test_missing_required_field_reported(field):
    row = dict(VALID_ROW)
    row[field] = ""
    issues = issues_for(row)
    assert any(i.field == field for i in issues)
    assert any("empty" in i.message for i in issues)


def test_malformed_source_url_reported():
    row = dict(VALID_ROW)
    row["source_url"] = "not-a-url"
    assert any(i.field == "source_url" for i in issues_for(row))
    row["source_url"] = "ftp://example.com/file"
    assert any(i.field == "source_url" for i in issues_for(row))


def test_invalid_verified_value_reported():
    row = dict(VALID_ROW)
    row["verified"] = "yes"
    assert any("invalid verified value: 'yes'" in i.message for i in issues_for(row))


def test_unknown_domain_reported():
    row = dict(VALID_ROW)
    row["domain"] = "space_law"
    assert any(i.field == "domain" for i in issues_for(row))


def test_invalid_document_type_reported():
    row = dict(VALID_ROW)
    row["document_type"] = "memo"
    assert any("invalid document_type" in i.message for i in issues_for(row))


def test_short_content_reported():
    row = dict(VALID_ROW)
    row["content"] = "short"
    assert any("suspiciously short" in i.message for i in issues_for(row))


def test_duplicate_row_reported():
    seen = {}
    assert validate_row(dict(VALID_ROW), 1, SEED_KEYS, seen) == []
    dup = dict(VALID_ROW)
    issues = validate_row(dup, 2, SEED_KEYS, seen)
    assert any("duplicate record" in i.message for i in issues)


# --------------------------------------------------------------------------- #
# file-level validation
# --------------------------------------------------------------------------- #

def test_validate_file_counts_valid_and_invalid(tmp_path):
    path = write_csv(tmp_path, [
        dict(VALID_ROW),
        {**VALID_ROW, "content": "", "verified": "yes"},
    ])
    report = validate_file(path)
    assert report.total == 2
    assert report.valid == 1
    assert report.invalid == 1
    assert 2 in report.issues


def test_validate_file_missing_required_column(tmp_path):
    bad = dict(VALID_ROW)
    bad.pop("content")
    path = write_csv(tmp_path, [bad])
    with pytest.raises(CsvFormatError) as exc:
        validate_file(path)
    assert "missing required columns" in str(exc.value)


# --------------------------------------------------------------------------- #
# UTF-8 / BOM / Nepali
# --------------------------------------------------------------------------- #

def test_nepali_utf8_preserved_with_bom(tmp_path):
    nepali_row = dict(VALID_ROW)
    nepali_row["content"] = "उपभोक्ता सम्पत्ति अदालत कानून। ग्राहक संरक्षण सम्बन्धी विवरण।"
    path = write_csv(tmp_path, [nepali_row], encoding="utf-8-sig")
    report = validate_file(path)
    assert report.valid == 1
    row = report.rows[0]
    assert "उपभोक्ता" in row.content
    assert "कानून" in row.content


def test_csv_file_with_nepali_is_parsed(tmp_path):
    path = tmp_path / "nepali.csv"
    path.write_text((
        "domain,document_title,document_type,content,source_name,source_url,verified\n"
        "consumer,उपभोक्ता संरक्षण,act," 
        "यो एक लामो उपभोक्ता संरक्षण विवरण हो जुन परीक्षणको लागि हो।,"
        "नेपाल कानून आयोग,https://example.invalid/nepali,true\n"
    ), encoding="utf-8")
    rows = read_rows(path)
    assert len(rows) == 1
    assert rows[0]["domain"] == "consumer"
    assert "उपभोक्ता" in rows[0]["document_title"]


def test_to_row_defaults():
    raw = dict(VALID_ROW)
    row = to_row(raw, 7)
    assert row.row_number == 7
    assert row.verified is True
    assert row.language == "nepali"
    assert row.provision_number == "1"


def test_to_row_defaults_false_verified():
    raw = dict(VALID_ROW)
    raw["verified"] = "false"
    assert to_row(raw, 1).verified is False