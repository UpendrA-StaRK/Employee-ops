"""Small shared serialization helpers for file-backed pipeline artifacts."""
from __future__ import annotations

from datetime import datetime


def json_default(value: object) -> str:
    """Serialize timestamps using the project's UTC ISO-8601 representation."""
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")
