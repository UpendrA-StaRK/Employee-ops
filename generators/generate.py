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
    --format STR        Output format: csv | json | both (default: both)

Examples:
    uv run python -m generators.generate --seed 42
    uv run python -m generators.generate --employees 500 --cases 2000 --scenario clean --seed 42
    uv run python -m generators.generate --scenario duplicates --seed 42
    uv run python -m generators.generate --format json --output-dir data/generated
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
VALID_FORMATS = ("csv", "json", "both")


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
        default="both",
        choices=VALID_FORMATS,
        dest="fmt",
        help="Output format: csv, json, or both (default: both)",
    )
    args = parser.parse_args(argv)

    # Validate positive counts
    if args.employees < 1:
        parser.error("--employees must be >= 1")
    if args.cases < 1:
        parser.error("--cases must be >= 1")

    return args


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

    write_csv = args.fmt in ("csv", "both")
    write_json = args.fmt in ("json", "both")

    if write_json:
        _write_json(output_dir / "employees.json", employees)
        _write_json(output_dir / "cases.json", cases)
        _write_json(output_dir / "case_history.json", case_history)

    if write_csv:
        _write_csv(output_dir / "employees.csv", employees)
        _write_csv(output_dir / "cases.csv", cases)
        _write_csv(output_dir / "case_history.csv", case_history)

    logger.info("Done. Output written to: %s", output_dir.resolve())
    return 0


if __name__ == "__main__":
    sys.exit(main())
