"""CLI entry point for the synthetic data generator.

Usage:
    uv run python -m generators.generate [OPTIONS]

Options:
    --employees INT     Number of employees to generate (default: 100)
    --cases INT         Number of cases to generate (default: 200)
    --scenario STR      Data scenario: clean | duplicates | missing_fields |
                        invalid_values | orphan_records (default: clean)
    --seed INT          Random seed for reproducibility (default: 42)
    --output-dir PATH   Output directory (default: data/generated)
    --format STR        Output format: csv | json | parquet | all (default: all)
                        Note: 'both' is a legacy alias for 'all' (csv + json + parquet).

Week 2 source formats:
    csv     → employees.csv, cases.csv, case_history.csv
    json    → employees.json, cases.json, case_history.json
    parquet → employees.parquet, cases.parquet, case_history.parquet

All three formats are derived from the same canonical in-memory dataset.
The generator is deterministic: identical --seed values always produce
identical output regardless of format.

Examples:
    uv run python -m generators.generate --seed 42
    uv run python -m generators.generate --employees 500 --cases 2000 --scenario clean --seed 42
    uv run python -m generators.generate --scenario duplicates --seed 42
    uv run python -m generators.generate --format json --output-dir data/generated
    uv run python -m generators.generate --format parquet --seed 42
    uv run python -m generators.generate --format all --seed 42
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
from pathlib import Path

from generators.generator import SyntheticDataGenerator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)

VALID_SCENARIOS = ("clean", "duplicates", "missing_fields", "invalid_values", "orphan_records")

# 'all' is the canonical multi-format value; 'both' is a legacy alias kept for
# backwards-compatibility with existing scripts and documentation.
VALID_FORMATS = ("csv", "json", "parquet", "all", "both")


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="generators.generate",
        description="Generate synthetic Employee Operations data for development and testing.",
    )
    parser.add_argument(
        "--employees",
        type=int,
        default=100,
        metavar="N",
        help="Number of employee records to generate (default: 100)",
    )
    parser.add_argument(
        "--cases",
        type=int,
        default=200,
        metavar="N",
        help="Number of case records to generate (default: 200)",
    )
    parser.add_argument(
        "--scenario",
        type=str,
        default="clean",
        choices=VALID_SCENARIOS,
        help="Data quality scenario to apply (default: clean)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible output (default: 42)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/generated",
        dest="output_dir",
        help="Directory to write generated files into (default: data/generated)",
    )
    parser.add_argument(
        "--format",
        type=str,
        default="all",
        choices=VALID_FORMATS,
        dest="fmt",
        help="Output format: csv, json, parquet, or all (default: all). 'both' is a legacy alias for 'all'.",
    )
    args = parser.parse_args(argv)

    # Validate positive counts
    if args.employees < 1:
        parser.error("--employees must be >= 1")
    if args.cases < 1:
        parser.error("--cases must be >= 1")

    return args


# ---------------------------------------------------------------------------
# Writers — each accepts a Path and a list of plain dicts
# ---------------------------------------------------------------------------

def _write_json(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(records, fh, indent=2, default=str)
    logger.info("Wrote %d records → %s", len(records), path)


def _write_csv(path: Path, records: list[dict]) -> None:
    if not records:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")
        logger.info("Wrote 0 records → %s", path)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(records[0].keys())
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    logger.info("Wrote %d records → %s", len(records), path)


def _write_parquet(path: Path, records: list[dict]) -> None:
    """Serialize records to Apache Parquet format using pyarrow.

    The records are first normalized so that ``None`` values become a typed
    null inside a ``pa.string()`` column (matching the string-dominant schema
    of the generator output). This preserves controlled bad-data scenarios
    (missing_fields, invalid_values) faithfully in the Parquet file.

    Args:
        path: Destination ``.parquet`` file path.
        records: List of plain dicts from the canonical generator dataset.
    """
    import pyarrow as pa
    import pyarrow.parquet as pq

    path.parent.mkdir(parents=True, exist_ok=True)

    if not records:
        # Write an empty Parquet file with no schema — valid and readable.
        table = pa.table({})
        pq.write_table(table, str(path))
        logger.info("Wrote 0 records → %s", path)
        return

    # Collect all field names (union of all records in case of heterogeneous rows)
    all_keys: list[str] = list(records[0].keys())

    # Build per-column lists; treat every column as nullable string so that
    # controlled bad-data (None, malformed strings) round-trips cleanly.
    columns: dict[str, list] = {k: [] for k in all_keys}
    for record in records:
        for k in all_keys:
            val = record.get(k)
            # Coerce non-string, non-None values to str so the schema is uniform.
            # None stays as None (becomes null in Parquet).
            columns[k].append(None if val is None else str(val))

    # Build a pyarrow Table with explicit nullable string schema
    schema = pa.schema([(k, pa.string()) for k in all_keys])
    arrays = [pa.array(columns[k], type=pa.string()) for k in all_keys]
    table = pa.Table.from_arrays(arrays, schema=schema)

    pq.write_table(table, str(path))
    logger.info("Wrote %d records → %s", len(records), path)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    output_dir = Path(args.output_dir)

    logger.info(
        "Generating dataset: scenario=%s seed=%d employees=%d cases=%d",
        args.scenario, args.seed, args.employees, args.cases,
    )

    gen = SyntheticDataGenerator(seed=args.seed)
    dataset = gen.generate(
        n_employees=args.employees,
        n_cases=args.cases,
        scenario=args.scenario,
    )

    employees = dataset["employees"]
    cases = dataset["cases"]
    case_history = dataset["case_history"]

    logger.info(
        "Generated: %d employees, %d cases, %d history records",
        len(employees), len(cases), len(case_history),
    )

    # 'both' is a legacy alias for 'all'
    fmt = args.fmt
    write_csv = fmt in ("csv", "all", "both")
    write_json = fmt in ("json", "all", "both")
    write_parquet = fmt in ("parquet", "all", "both")

    if write_json:
        _write_json(output_dir / "employees.json", employees)
        _write_json(output_dir / "cases.json", cases)
        _write_json(output_dir / "case_history.json", case_history)

    if write_csv:
        _write_csv(output_dir / "employees.csv", employees)
        _write_csv(output_dir / "cases.csv", cases)
        _write_csv(output_dir / "case_history.csv", case_history)

    if write_parquet:
        _write_parquet(output_dir / "employees.parquet", employees)
        _write_parquet(output_dir / "cases.parquet", cases)
        _write_parquet(output_dir / "case_history.parquet", case_history)

    logger.info("Done. Output written to: %s", output_dir.resolve())
    return 0


if __name__ == "__main__":
    sys.exit(main())
