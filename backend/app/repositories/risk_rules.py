"""Repository for risk_rules."""

from __future__ import annotations

from typing import Any, Sequence
from uuid import uuid4

from psycopg.types.json import Jsonb

from app.repositories.base import BaseRepository


class RiskRuleRepository(BaseRepository):
    def create(
        self,
        key: str,
        label: str,
        patterns: list,
        severity: str,
        domain_id=None,
        description: str | None = None,
        is_active: bool = True,
    ) -> dict[str, Any]:
        row_id = uuid4()
        self._execute(
            """
            INSERT INTO risk_rules (id, domain_id, key, label, description, patterns, severity, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (row_id, domain_id, key, label, description, Jsonb(patterns), severity, is_active),
        )
        return self.get_by_id(row_id)  # type: ignore[return-value]

    def get_by_id(self, rule_id) -> dict[str, Any] | None:
        return self._fetch_one(
            "SELECT * FROM risk_rules WHERE id = %s", (rule_id,)
        )

    def get_by_key(self, key: str) -> dict[str, Any] | None:
        return self._fetch_one(
            "SELECT * FROM risk_rules WHERE key = %s", (key,)
        )

    def find_active(self) -> list[dict[str, Any]]:
        return self._fetch_all(
            "SELECT * FROM risk_rules WHERE is_active = TRUE ORDER BY key"
        )