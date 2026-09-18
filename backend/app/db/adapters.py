"""Global psycopg adapters for JSONB columns.

Registering the default JSON loader globally (on ``psycopg.adapters``) means
every connection created after this import returns ``jsonb`` values as plain
Python objects instead of opaque text wrappers.

Import this module for its side effect, e.g. in repositories/base.py:
    from app.db import adapters  # noqa: F401
"""

import json

from psycopg.types.json import set_json_loads

set_json_loads(json.loads)