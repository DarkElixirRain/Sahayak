"""Repository for court_cases."""

from __future__ import annotations

from typing import Any, Sequence
from uuid import uuid4

from app.repositories.base import BaseRepository


class CourtCaseRepository(BaseRepository):
    def create(
        self,
        court_name: str,
        domain_id=None,
        case_number: str | None = None,
        decision_date=None,
        title: str | None = None,
        case_type: str | None = None,
        facts_summary: str | None = None,
        legal_issues: str | None = None,
        decision_summary: str | None = None,
        official_url: str | None = None,
        source_id=None,
        is_verified: bool = False,
        verified_at=None,
    ) -> dict[str, Any]:
        row_id = uuid4()
        self._execute(
            """
            INSERT INTO court_cases (
                id, domain_id, court_name, case_number, decision_date, title,
                case_type, facts_summary, legal_issues, decision_summary,
                official_url, source_id, is_verified, verified_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                row_id, domain_id, court_name, case_number, decision_date, title,
                case_type, facts_summary, legal_issues, decision_summary,
                official_url, source_id, is_verified, verified_at,
            ),
        )
        return self.get_by_id(row_id)  # type: ignore[return-value]

    def get_by_id(self, case_id) -> dict[str, Any] | None:
        return self._fetch_one(
            "SELECT * FROM court_cases WHERE id = %s", (case_id,)
        )

    def find_by_domain(
        self, domain_id, verified_only: bool = True
    ) -> list[dict[str, Any]]:
        verified = "AND is_verified = TRUE" if verified_only else ""
        return self._fetch_all(
            f"""
            SELECT * FROM court_cases
            WHERE domain_id = %s {verified} ORDER BY decision_date DESC NULLS LAST
            """,
            (domain_id,),
        )