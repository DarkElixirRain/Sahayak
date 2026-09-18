"""Privacy-by-design checks (no database required).

Sahayak must never persist secrets: passwords, OTPs, PINs, bank credentials,
API keys, or unnecessary PII. These tests statically verify the schema cannot
contain such columns and that no such values are embedded in source code.
"""

import re
from pathlib import Path

from app.services.csv_importer import MIN_CONTENT_LENGTH

BACKEND = Path(__file__).resolve().parents[1]
MIGRATIONS = BACKEND / "app" / "db" / "migrations"

FORBIDDEN_WORDS = ("otp", "password", "pin", "api_key", "secret", "private_key")


def _migration_sql() -> str:
    return "\n".join(
        p.read_text(encoding="utf-8")
        for p in sorted(MIGRATIONS.glob("*.sql"))
    )


def test_no_secret_columns_in_schema():
    sql = _migration_sql()
    for word in FORBIDDEN_WORDS:
        assert re.search(rf"\b{re.escape(word)}\b", sql, re.IGNORECASE) is None, (
            f"schema references forbidden secret column/word: {word!r}"
        )


def test_secret_values_never_hardcoded_in_app_code():
    for path in (BACKEND / "app").rglob("*.py"):
        if "pycache" in str(path):
            continue
        text = path.read_text(encoding="utf-8")
        for token in ("postgresql://", "gsk_", "npg_", "BEGIN PRIVATE"):
            assert token not in text, f"{path.name} may embed a secret value"


def test_min_content_threshold_is_sane():
    assert MIN_CONTENT_LENGTH >= 3


def test_conversation_privacy_comment_exists():
    sql = _migration_sql()
    assert "never store passwords" in sql
    assert "OTPs" in sql


def test_scripts_never_print_connection_string():
    for path in sorted((BACKEND / "scripts").glob("*.py")):
        text = path.read_text(encoding="utf-8")
        assert "print(settings.database_url" not in text
        assert "print(database_url" not in text
        assert "postgresql://" not in text