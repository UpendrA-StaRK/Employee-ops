"""RAW layer for the Enterprise Data Pipeline.

The RAW layer sits immediately after ingestion. Its sole responsibility is to:

  1. Wrap every ingested record in a metadata envelope (RawRecord).
  2. Preserve the original source value byte-for-byte — no cleaning, no renaming.
  3. Persist the batch to disk at data/raw/{run_id}/{source_system}.json
     so that each pipeline run is independently inspectable and re-processable.

Pipeline position:
    Source
      ↓
    Ingestion  (app/pipelines/ingestion.py, db_ingestion.py, rest_ingestion.py)
      ↓
    RAW        ← this module
      ↓
    Standardization  (app/pipelines/standardize.py)

What the RAW layer does NOT do:
  - rename fields
  - convert data types
  - strip whitespace
  - fix dates
  - reject invalid records
  - perform joins or lookups
  - apply business rules
"""
from __future__ import annotations

import json
import logging
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Root directory for RAW output.  Override in tests via RAW_BASE_DIR.
_DEFAULT_RAW_DIR = Path(__file__).parent.parent.parent / "data" / "raw"


@dataclass
class RawRecord:
    """One source record wrapped in pipeline metadata.

    Attributes:
        run_id:          Unique identifier for this pipeline run.
                         All records processed in a single invocation share the
                         same run_id, making it easy to re-process or audit a run.
        source_system:   Human-readable name for the originating source system
                         (e.g. "employees_csv", "cases_json", "rest_departments").
        source_type:     Technical format / protocol: "csv", "json", "parquet",
                         "postgresql", "rest".
        ingested_at:     UTC timestamp when this record entered the pipeline.
        payload:         The original record exactly as returned by the ingestion
                         layer — a plain dict, values unmodified.
        source_location: Optional file path, URL, or table name that identifies
                         where the record came from within the source system.
    """

    run_id: str
    source_system: str
    source_type: str
    ingested_at: str          # ISO-8601 string so it is trivially JSON-serialisable
    payload: dict[str, Any]
    source_location: str = ""


def create_run_id() -> str:
    """Generate a fresh pipeline run identifier (UUID4)."""
    return str(uuid.uuid4())


def wrap_records(
    records: list[dict[str, Any]],
    *,
    run_id: str,
    source_system: str,
    source_type: str,
    source_location: str = "",
) -> list[RawRecord]:
    """Wrap a list of ingested records in RAW metadata envelopes.

    Args:
        records:         Output from any ingestion function (list of dicts).
        run_id:          Pipeline run identifier (share across all sources in one run).
        source_system:   Name of the source system, e.g. ``"employees_csv"``.
        source_type:     Format of the source: ``"csv"``, ``"json"``, ``"parquet"``,
                         ``"postgresql"``, ``"rest"``.
        source_location: Optional path/URL/table identifying the exact source location.

    Returns:
        List of :class:`RawRecord` objects preserving every source value exactly.
    """
    ingested_at = datetime.now(timezone.utc).isoformat()
    raw_records = [
        RawRecord(
            run_id=run_id,
            source_system=source_system,
            source_type=source_type,
            ingested_at=ingested_at,
            payload=record,           # original dict, untouched
            source_location=source_location,
        )
        for record in records
    ]
    logger.info(
        "RAW wrap complete | source_system=%s source_type=%s run_id=%s records=%d",
        source_system,
        source_type,
        run_id,
        len(raw_records),
    )
    return raw_records


def persist_raw(
    raw_records: list[RawRecord],
    base_dir: Path | None = None,
) -> Path:
    """Write RAW records to disk as a JSON file.

    Output path: ``<base_dir>/<run_id>/<source_system>.json``

    A JSON array is written, where each element is the dict representation of
    a :class:`RawRecord`.  This format is human-readable and easy to inspect
    during development.

    Args:
        raw_records: Records produced by :func:`wrap_records`.
        base_dir:    Root directory for RAW output.  Defaults to
                     ``data/raw/`` relative to the repository root.

    Returns:
        Path to the written file.

    Raises:
        ValueError: If ``raw_records`` is empty (nothing to write).
    """
    if not raw_records:
        raise ValueError("No RAW records to persist.")

    root = base_dir or _DEFAULT_RAW_DIR
    run_dir = root / raw_records[0].run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    output_path = run_dir / f"{raw_records[0].source_system}.json"
    with output_path.open("w", encoding="utf-8") as f:
        json.dump([asdict(r) for r in raw_records], f, indent=2, default=str)

    logger.info(
        "RAW persisted | path=%s records=%d",
        output_path,
        len(raw_records),
    )
    return output_path


def load_raw(path: Path) -> list[RawRecord]:
    """Load RAW records previously written by :func:`persist_raw`.

    Args:
        path: Path to a RAW JSON file.

    Returns:
        List of :class:`RawRecord` objects.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not path.exists():
        raise FileNotFoundError(f"RAW file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    return [RawRecord(**item) for item in data]
