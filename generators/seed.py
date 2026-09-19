"""Database seeder for the Employee Operations AI development environment.

Reads generated synthetic data from data/generated/ and inserts it into
the development database using the existing SQLAlchemy session.

SAFE BY DEFAULT:
    Records whose primary key already exists in the database are SKIPPED.
    Existing developer data is never deleted unless --clean is explicitly passed.

DESTRUCTIVE MODE (--clean):
    Truncates case_history → cases → employees (FK-safe order) before inserting.
    Use this to get a fresh, clean development dataset.

Usage:
    # Non-destructive: insert missing records only
    uv run python -m generators.seed

    # Destructive: wipe and reload
    uv run python -m generators.seed --clean

    # Use a different seed or scenario
    uv run python -m generators.seed --seed 99 --employees 50 --cases 100

    # Seed from already-generated files instead of regenerating
    uv run python -m generators.seed --from-files data/generated
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="generators.seed",
        description="Seed the development database with synthetic data.",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="DESTRUCTIVE: truncate existing data before seeding.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for synthetic data generation (default: 42).",
    )
    parser.add_argument(
        "--employees",
        type=int,
        default=100,
        metavar="N",
        help="Number of employees to generate (default: 100).",
    )
    parser.add_argument(
        "--cases",
        type=int,
        default=200,
        metavar="N",
        help="Number of cases to generate (default: 200).",
    )
    parser.add_argument(
        "--from-files",
        type=str,
        default=None,
        dest="from_files",
        metavar="DIR",
        help=(
            "Load from pre-generated JSON files in DIR instead of regenerating. "
            "Expects employees.json, cases.json, case_history.json."
        ),
    )
    return parser.parse_args(argv)


def _load_from_files(directory: str) -> dict[str, list[dict]]:
    """Load pre-generated JSON files."""
    base = Path(directory)
    result: dict[str, list[dict]] = {}
    for name in ("employees", "cases", "case_history"):
        path = base / f"{name}.json"
        if not path.exists():
            logger.error("Expected file not found: %s", path)
            sys.exit(1)
        with path.open("r", encoding="utf-8") as fh:
            result[name] = json.load(fh)
    return result


def _generate_in_memory(seed: int, n_employees: int, n_cases: int) -> dict[str, list[dict]]:
    """Generate dataset in memory (clean scenario only for seeding)."""
    from generators.generator import SyntheticDataGenerator
    gen = SyntheticDataGenerator(seed=seed)
    return gen.generate(n_employees=n_employees, n_cases=n_cases, scenario="clean")


def _dt(value: str | None) -> "datetime | None":
    """Parse ISO timestamp string to datetime, or return None."""
    if value is None:
        return None
    # Replace Z suffix if present
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    # --- Import application dependencies here (not at module level) ---
    # This keeps the import-time footprint small when the module is imported
    # by tests without a database being available.
    try:
        from sqlalchemy.orm import Session
        from app.db.session import SessionLocal
        from app.models.employee import Employee
        from app.models.case import Case, CaseStatus, CaseCategory, CasePriority
        from app.models.case_history import CaseHistory
    except ImportError as exc:
        logger.error("Failed to import application modules: %s", exc)
        logger.error("Ensure the virtual environment is activated and dependencies are installed.")
        return 1

    # --- Load dataset ---
    if args.from_files:
        logger.info("Loading from files: %s", args.from_files)
        dataset = _load_from_files(args.from_files)
    else:
        logger.info(
            "Generating clean dataset in-memory: seed=%d employees=%d cases=%d",
            args.seed, args.employees, args.cases,
        )
        dataset = _generate_in_memory(
            seed=args.seed, n_employees=args.employees, n_cases=args.cases
        )

    employees_data = dataset["employees"]
    cases_data = dataset["cases"]
    history_data = dataset["case_history"]

    logger.info(
        "Dataset ready: %d employees, %d cases, %d history records",
        len(employees_data), len(cases_data), len(history_data),
    )

    db: Session = SessionLocal()
    try:
        if args.clean:
            logger.warning(
                "--clean flag set. Deleting all case_history → cases → employees records."
            )
            db.query(CaseHistory).delete()
            db.query(Case).delete()
            db.query(Employee).delete()
            db.commit()
            logger.info("Tables truncated.")

        # --- Seed employees ---
        existing_employee_ids: set[str] = {
            row[0] for row in db.query(Employee.employee_id).all()
        }
        employees_to_insert = [
            e for e in employees_data if e["employee_id"] not in existing_employee_ids
        ]
        logger.info(
            "Employees: %d in dataset, %d existing → inserting %d",
            len(employees_data), len(existing_employee_ids), len(employees_to_insert),
        )
        for e in employees_to_insert:
            db.add(Employee(
                employee_id=e["employee_id"],
                name=e.get("name") or "Unknown",
                email=e.get("email") or f"{e['employee_id']}@placeholder.com",
                department=e.get("department") or "General",
                job_title=e.get("job_title") or "Employee",
                status=e.get("status") or "ACTIVE",
                created_at=_dt(e.get("created_at")),
                updated_at=_dt(e.get("updated_at")),
            ))
        db.flush()

        # --- Seed cases ---
        existing_case_ids: set[str] = {
            row[0] for row in db.query(Case.case_id).all()
        }
        # Only insert cases whose employee_id exists in the DB
        valid_employee_ids = {
            row[0] for row in db.query(Employee.employee_id).all()
        }
        cases_to_insert = [
            c for c in cases_data
            if c["case_id"] not in existing_case_ids
            and c.get("employee_id") in valid_employee_ids
        ]
        logger.info(
            "Cases: %d in dataset, %d existing → inserting %d",
            len(cases_data), len(existing_case_ids), len(cases_to_insert),
        )
        for c in cases_to_insert:
            db.add(Case(
                case_id=c["case_id"],
                employee_id=c["employee_id"],
                category=CaseCategory(c["category"]),
                subject=c.get("subject") or "Untitled",
                description=c.get("description") or "",
                status=CaseStatus(c.get("status") or "OPEN"),
                priority=CasePriority(c.get("priority") or "MEDIUM"),
                created_at=_dt(c.get("created_at")),
                updated_at=_dt(c.get("updated_at")),
            ))
        db.flush()

        # --- Seed case history ---
        existing_history_ids: set[str] = {
            row[0] for row in db.query(CaseHistory.history_id).all()
        }
        valid_case_ids = {row[0] for row in db.query(Case.case_id).all()}
        history_to_insert = [
            h for h in history_data
            if h["history_id"] not in existing_history_ids
            and h.get("case_id") in valid_case_ids
        ]
        logger.info(
            "History: %d in dataset, %d existing → inserting %d",
            len(history_data), len(existing_history_ids), len(history_to_insert),
        )
        for h in history_to_insert:
            old_st = h.get("old_status")
            db.add(CaseHistory(
                history_id=h["history_id"],
                case_id=h["case_id"],
                old_status=CaseStatus(old_st) if old_st else None,
                new_status=CaseStatus(h["new_status"]),
                comment=h.get("comment"),
                changed_by=h.get("changed_by") or "system",
                created_at=_dt(h.get("created_at")),
            ))

        db.commit()
        logger.info("Seeding complete.")
    except Exception:
        db.rollback()
        logger.error("Seeding failed — transaction rolled back.", exc_info=True)
        return 1
    finally:
        db.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
