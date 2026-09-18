"""Persistence record base.

The Sahayak database phase will add concrete records (scenarios, sources,
risk rules, incidents) as subclasses of ``BaseRecord``. ``row_factory()``
returns a psycopg ``class_row`` factory so repositories can map database
rows directly onto records without an ORM.
"""

from dataclasses import dataclass
from typing import Any

from psycopg.rows import class_row


@dataclass(frozen=True)
class BaseRecord:
    @classmethod
    def row_factory(cls) -> Any:
        return class_row(cls)