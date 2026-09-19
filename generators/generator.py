"""Core synthetic data generator for Employee Operations AI.

This module is self-contained and uses only the Python standard library.
It does NOT import from the application package (app.*).

The generator is deterministic: instantiate SyntheticDataGenerator with a
fixed seed and identical calls always produce identical datasets.

Lifecycle transition rules mirror ALLOWED_TRANSITIONS in app/services/case.py.
They are intentionally duplicated here so the generator has no dependency on
the production application at runtime.

    OPEN        -> IN_PROGRESS, CLOSED
    IN_PROGRESS -> PENDING, RESOLVED
    PENDING     -> IN_PROGRESS, RESOLVED
    RESOLVED    -> CLOSED, IN_PROGRESS
    CLOSED      -> (terminal)
"""
from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

# ---------------------------------------------------------------------------
# Transition rules — duplicated from app/services/case.py intentionally so
# this module has zero dependency on the production application.
# ---------------------------------------------------------------------------

ALLOWED_TRANSITIONS: dict[str, list[str]] = {
    "OPEN":        ["IN_PROGRESS", "CLOSED"],
    "IN_PROGRESS": ["PENDING", "RESOLVED"],
    "PENDING":     ["IN_PROGRESS", "RESOLVED"],
    "RESOLVED":    ["CLOSED", "IN_PROGRESS"],
    "CLOSED":      [],
}

TERMINAL_STATUSES = {"CLOSED"}

# ---------------------------------------------------------------------------
# Realistic data pools — no external library required
# ---------------------------------------------------------------------------

FIRST_NAMES = [
    "Aarav", "Priya", "Rahul", "Sneha", "Vikram", "Ananya", "Rohan", "Divya",
    "Kiran", "Meera", "Arjun", "Pooja", "Neel", "Kavya", "Siddharth", "Riya",
    "Amit", "Shreya", "Nikhil", "Aditi", "Raj", "Swati", "Varun", "Deepika",
    "Arun", "Sunita", "Manoj", "Rekha", "Suresh", "Lata", "Ravi", "Geeta",
    "Sanjay", "Usha", "Vinod", "Nirmala", "Rajesh", "Savita", "Ashok", "Padma",
    "James", "Sarah", "Michael", "Emily", "David", "Jessica", "Robert", "Laura",
    "John", "Lisa", "Chris", "Karen", "Daniel", "Amy", "Paul", "Sandra",
]

LAST_NAMES = [
    "Sharma", "Patel", "Singh", "Kumar", "Mehta", "Gupta", "Joshi", "Verma",
    "Nair", "Reddy", "Rao", "Iyer", "Pillai", "Menon", "Krishnan", "Chandra",
    "Bose", "Das", "Roy", "Sen", "Banerjee", "Chatterjee", "Mukherjee", "Ghosh",
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Martinez",
    "Wilson", "Anderson", "Taylor", "Thomas", "Moore", "Jackson", "Martin",
]

DEPARTMENTS = [
    "Human Resources",
    "Finance",
    "Information Technology",
    "Operations",
    "Legal",
    "Compliance",
    "Sales",
    "Marketing",
    "Engineering",
    "Customer Success",
]

JOB_TITLES: dict[str, list[str]] = {
    "Human Resources": ["HR Business Partner", "Talent Acquisition Specialist", "HR Coordinator", "HR Manager"],
    "Finance": ["Financial Analyst", "Accounts Manager", "Senior Accountant", "Finance Controller"],
    "Information Technology": ["Software Engineer", "Systems Administrator", "IT Support Analyst", "DevOps Engineer"],
    "Operations": ["Operations Analyst", "Operations Manager", "Process Improvement Specialist", "Logistics Coordinator"],
    "Legal": ["Legal Counsel", "Paralegal", "Compliance Analyst", "Legal Associate"],
    "Compliance": ["Compliance Officer", "Risk Analyst", "Regulatory Specialist", "Audit Associate"],
    "Sales": ["Account Executive", "Sales Manager", "Business Development Representative", "Sales Analyst"],
    "Marketing": ["Marketing Analyst", "Content Strategist", "Digital Marketing Specialist", "Brand Manager"],
    "Engineering": ["Data Engineer", "Machine Learning Engineer", "Platform Engineer", "Solutions Architect"],
    "Customer Success": ["Customer Success Manager", "Support Specialist", "Implementation Consultant", "Account Manager"],
}

EMAIL_DOMAINS = ["kpmg-internal.com", "corp.example.com", "enterprise.io", "hr-portal.net"]

EMPLOYEE_STATUSES = ["ACTIVE", "ACTIVE", "ACTIVE", "ACTIVE", "INACTIVE"]  # weighted toward ACTIVE

CATEGORIES = ["LEAVE", "PAYROLL", "BENEFITS", "ACCESS", "GENERAL"]

PRIORITIES = ["LOW", "MEDIUM", "MEDIUM", "HIGH", "URGENT"]  # weighted toward MEDIUM

CASE_SUBJECTS: dict[str, list[str]] = {
    "LEAVE": [
        "Annual leave balance discrepancy",
        "Sick leave approval request",
        "Maternity leave documentation",
        "Leave encashment query",
        "Emergency leave request",
        "Parental leave policy clarification",
    ],
    "PAYROLL": [
        "Salary not credited for current month",
        "Incorrect tax deduction applied",
        "Overtime pay calculation error",
        "Incentive payout discrepancy",
        "Provident fund contribution mismatch",
        "Bonus payment not received",
    ],
    "BENEFITS": [
        "Health insurance claim rejected",
        "Dental coverage enrollment issue",
        "Employee stock plan query",
        "Life insurance nominee update",
        "Wellness allowance reimbursement",
        "Flexible benefits plan change",
    ],
    "ACCESS": [
        "VPN access not working after laptop replacement",
        "Application permission denied",
        "Badge access to new floor required",
        "Email account locked out",
        "New hire system provisioning incomplete",
        "Two-factor authentication reset",
    ],
    "GENERAL": [
        "Relocation assistance policy query",
        "Performance review process clarification",
        "Training and development budget request",
        "Workplace harassment concern",
        "Remote work policy clarification",
        "Equipment replacement request",
    ],
}

CASE_DESCRIPTIONS: dict[str, list[str]] = {
    "LEAVE": [
        "Employee reports that the leave balance shown in the self-service portal does not match the approved leave records.",
        "Requesting approval for sick leave from next week pending medical documentation.",
        "Employee requires guidance on maternity leave entitlements and documentation requirements.",
        "Querying eligibility and process for converting unused leave days to cash equivalent.",
    ],
    "PAYROLL": [
        "Employee salary for the current month has not been credited to the bank account as of today.",
        "Tax deduction appears incorrect compared to the submitted investment declaration.",
        "Overtime hours worked in the previous period have not been reflected in the salary slip.",
        "The annual incentive payout communicated by the manager does not match the amount received.",
    ],
    "BENEFITS": [
        "Insurance claim for a recent hospitalization was rejected citing a pre-existing condition clause.",
        "Employee is unable to enroll a dependent in the dental coverage plan through the HR portal.",
        "Query regarding vesting schedule and current valuation of the employee stock option grant.",
        "Requesting update of life insurance policy nominee details following a family change.",
    ],
    "ACCESS": [
        "After receiving a replacement laptop, the VPN client refuses to authenticate.",
        "Receiving permission denied errors when attempting to access a required business application.",
        "New office floor requires a badge access update that has not been processed.",
        "Account is locked after multiple failed login attempts and self-service reset is not working.",
    ],
    "GENERAL": [
        "Requesting details on relocation assistance available for an upcoming inter-city transfer.",
        "Seeking clarification on the mid-year performance review timeline and evaluation criteria.",
        "Requesting approval to use the learning and development budget for an external certification course.",
        "Raising a concern about workplace conduct that is affecting team productivity and morale.",
    ],
}

COMMENTS_POOL = [
    "Acknowledged. Investigating with the relevant team.",
    "Additional documentation requested from the employee.",
    "Escalated to the payroll department for review.",
    "Pending response from the IT team.",
    "HR has reviewed the case and is following up.",
    "Resolved after updating the employee records.",
    "Closed — no further action required.",
    "Case forwarded to the benefits administration team.",
    "Employee confirmed receipt of resolution.",
    "Waiting for manager approval before proceeding.",
    None,  # some history entries have no comment
    None,
]


# ---------------------------------------------------------------------------
# Generator class
# ---------------------------------------------------------------------------

class SyntheticDataGenerator:
    """Deterministic synthetic data generator.

    All randomness is sourced from a single ``random.Random`` instance
    seeded at construction time. This guarantees identical output for
    identical seeds regardless of external state.

    Args:
        seed: Integer seed for deterministic generation. Default: 42.
    """

    def __init__(self, seed: int = 42) -> None:
        self.seed = seed
        self._rng = random.Random(seed)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _uuid(self) -> str:
        """Generate a UUID that is driven by our seeded RNG."""
        return str(uuid.UUID(int=self._rng.getrandbits(128), version=4))

    def _ts(self, base: datetime, delta_seconds: int = 0) -> str:
        """Return an ISO-8601 UTC timestamp string."""
        return (base + timedelta(seconds=delta_seconds)).isoformat()

    def _random_past_datetime(self, days_back: int = 365) -> datetime:
        """Return a random UTC datetime within the past ``days_back`` days."""
        offset_seconds = self._rng.randint(0, days_back * 86400)
        return datetime(2025, 9, 18, tzinfo=timezone.utc) - timedelta(seconds=offset_seconds)

    def _pick(self, sequence: list[Any]) -> Any:
        """Pick one element from a list using the seeded RNG."""
        return sequence[self._rng.randrange(len(sequence))]

    # ------------------------------------------------------------------
    # Employee generation
    # ------------------------------------------------------------------

    def generate_employees(
        self, count: int = 100, scenario: str = "clean"
    ) -> list[dict[str, Any]]:
        """Generate ``count`` synthetic employee records.

        In the ``clean`` scenario every record is fully valid.
        Mutation scenarios introduce controlled defects.

        Args:
            count: Number of employees to generate.
            scenario: One of ``clean``, ``duplicates``, ``missing_fields``,
                ``invalid_values``, ``orphan_records``.

        Returns:
            List of employee dictionaries compatible with the Employee model.
        """
        employees: list[dict[str, Any]] = []
        used_emails: set[str] = set()

        for i in range(count):
            first = self._pick(FIRST_NAMES)
            last = self._pick(LAST_NAMES)
            department = self._pick(DEPARTMENTS)
            job_title = self._pick(JOB_TITLES[department])
            domain = self._pick(EMAIL_DOMAINS)
            # Ensure unique email in clean scenario
            email_base = f"{first.lower()}.{last.lower()}"
            email = f"{email_base}@{domain}"
            suffix = 1
            while email in used_emails:
                email = f"{email_base}{suffix}@{domain}"
                suffix += 1
            used_emails.add(email)

            created_at = self._random_past_datetime(days_back=730)
            updated_at = created_at + timedelta(seconds=self._rng.randint(0, 86400 * 30))

            record: dict[str, Any] = {
                "employee_id": self._uuid(),
                "name": f"{first} {last}",
                "email": email,
                "department": department,
                "job_title": job_title,
                "status": self._pick(EMPLOYEE_STATUSES),
                "created_at": created_at.isoformat(),
                "updated_at": updated_at.isoformat(),
            }
            employees.append(record)

        # --- Scenario mutations ---
        if scenario == "duplicates" and len(employees) > 1:
            # Duplicate ~5% of records (same employee_id and email)
            n_dupes = max(1, count // 20)
            for _ in range(n_dupes):
                source = self._pick(employees)
                employees.append(dict(source))

        elif scenario == "missing_fields" and employees:
            n_missing = max(1, count // 10)
            fields_to_null = ["name", "email", "department", "job_title"]
            for idx in self._rng.sample(range(len(employees)), min(n_missing, len(employees))):
                field = self._pick(fields_to_null)
                employees[idx][field] = None

        elif scenario == "invalid_values" and employees:
            n_invalid = max(1, count // 10)
            for idx in self._rng.sample(range(len(employees)), min(n_invalid, len(employees))):
                mutation = self._rng.randint(0, 2)
                if mutation == 0:
                    employees[idx]["email"] = "NOT_AN_EMAIL"
                elif mutation == 1:
                    employees[idx]["status"] = "ZOMBIE"
                else:
                    employees[idx]["created_at"] = "not-a-date"

        # orphan_records only affects case/history; no employee-level mutations needed
        return employees

    # ------------------------------------------------------------------
    # Case generation
    # ------------------------------------------------------------------

    def generate_cases(
        self,
        employees: list[dict[str, Any]],
        count: int = 200,
        scenario: str = "clean",
    ) -> list[dict[str, Any]]:
        """Generate ``count`` synthetic case records.

        In the ``clean`` scenario every ``employee_id`` references a record
        in ``employees``.

        Args:
            employees: List of employee dicts produced by :meth:`generate_employees`.
            count: Number of cases to generate.
            scenario: Scenario name controlling defect injection.

        Returns:
            List of case dictionaries compatible with the Case model.
        """
        if not employees:
            return []

        valid_employee_ids = [e["employee_id"] for e in employees]
        cases: list[dict[str, Any]] = []

        for _ in range(count):
            category = self._pick(CATEGORIES)
            created_at = self._random_past_datetime(days_back=365)
            # status will be overwritten by generate_case_history; set OPEN here
            record: dict[str, Any] = {
                "case_id": self._uuid(),
                "employee_id": self._pick(valid_employee_ids),
                "category": category,
                "subject": self._pick(CASE_SUBJECTS[category]),
                "description": self._pick(CASE_DESCRIPTIONS[category]),
                "status": "OPEN",
                "priority": self._pick(PRIORITIES),
                "created_at": created_at.isoformat(),
                "updated_at": created_at.isoformat(),
            }
            cases.append(record)

        # --- Scenario mutations ---
        if scenario == "duplicates" and len(cases) > 1:
            n_dupes = max(1, count // 20)
            for _ in range(n_dupes):
                cases.append(dict(self._pick(cases)))

        elif scenario == "missing_fields" and cases:
            n_missing = max(1, count // 10)
            fields_to_null = ["subject", "description", "category"]
            for idx in self._rng.sample(range(len(cases)), min(n_missing, len(cases))):
                cases[idx][self._pick(fields_to_null)] = None

        elif scenario == "invalid_values" and cases:
            n_invalid = max(1, count // 10)
            for idx in self._rng.sample(range(len(cases)), min(n_invalid, len(cases))):
                mutation = self._rng.randint(0, 2)
                if mutation == 0:
                    cases[idx]["status"] = "FLYING"
                elif mutation == 1:
                    cases[idx]["priority"] = "SUPER_DUPER_URGENT"
                else:
                    cases[idx]["category"] = "MADE_UP"

        elif scenario == "orphan_records" and cases:
            n_orphans = max(1, count // 10)
            for idx in self._rng.sample(range(len(cases)), min(n_orphans, len(cases))):
                cases[idx]["employee_id"] = self._uuid()  # nonexistent employee

        return cases

    # ------------------------------------------------------------------
    # Case history generation
    # ------------------------------------------------------------------

    def generate_case_history(
        self,
        cases: list[dict[str, Any]],
        scenario: str = "clean",
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Generate case history records and update terminal case statuses.

        Every case receives at least one history entry (the creation event
        with ``old_status=None``, ``new_status=OPEN``). Additional
        transitions are generated following the allowed lifecycle.

        The function also updates ``case["status"]`` and ``case["updated_at"]``
        in-place so they reflect the final state of the history chain.

        Args:
            cases: List of case dicts (mutated in-place to sync terminal status).
            scenario: Scenario name controlling defect injection.

        Returns:
            Tuple of (updated_cases, history_records).
        """
        if not cases:
            return cases, []

        valid_case_ids = {c["case_id"] for c in cases}
        history: list[dict[str, Any]] = []

        for case in cases:
            case_id = case["case_id"]
            case_created_at = datetime.fromisoformat(case["created_at"])

            # Build the transition chain starting at OPEN
            current_status: str = "OPEN"
            current_ts = case_created_at
            chain: list[tuple[str | None, str, datetime]] = []

            # Initial creation event
            chain.append((None, "OPEN", current_ts))

            # Simulate 0–4 additional transitions (weighted toward shorter chains)
            n_extra = self._rng.choices([0, 1, 2, 3, 4], weights=[10, 35, 30, 15, 10])[0]
            for _ in range(n_extra):
                choices = ALLOWED_TRANSITIONS.get(current_status, [])
                if not choices:
                    break
                next_status = self._pick(choices)
                current_ts = current_ts + timedelta(seconds=self._rng.randint(3600, 86400 * 7))
                chain.append((current_status, next_status, current_ts))
                current_status = next_status

            # Update case's terminal status and updated_at to match end of chain
            case["status"] = current_status
            case["updated_at"] = current_ts.isoformat()

            # Write history records
            for old_st, new_st, ts in chain:
                history.append({
                    "history_id": self._uuid(),
                    "case_id": case_id,
                    "old_status": old_st,
                    "new_status": new_st,
                    "comment": self._pick(COMMENTS_POOL),
                    "changed_by": "system",
                    "created_at": ts.isoformat(),
                })

        # --- Scenario mutations ---
        if scenario == "invalid_values" and history:
            n_invalid = max(1, len(history) // 20)
            for idx in self._rng.sample(range(len(history)), min(n_invalid, len(history))):
                history[idx]["new_status"] = "INVALID_STATE"

        elif scenario == "orphan_records" and history:
            n_orphans = max(1, len(history) // 20)
            for idx in self._rng.sample(range(len(history)), min(n_orphans, len(history))):
                history[idx]["case_id"] = self._uuid()  # nonexistent case

        return cases, history

    # ------------------------------------------------------------------
    # Convenience: generate full dataset in one call
    # ------------------------------------------------------------------

    def generate(
        self,
        n_employees: int = 100,
        n_cases: int = 200,
        scenario: str = "clean",
    ) -> dict[str, list[dict[str, Any]]]:
        """Generate a complete synthetic dataset.

        Args:
            n_employees: Number of employees to generate.
            n_cases: Number of cases to generate.
            scenario: Scenario variant.

        Returns:
            Dictionary with keys ``employees``, ``cases``, ``case_history``.
        """
        employees = self.generate_employees(count=n_employees, scenario=scenario)
        cases = self.generate_cases(employees=employees, count=n_cases, scenario=scenario)
        cases, history = self.generate_case_history(cases=cases, scenario=scenario)
        return {
            "employees": employees,
            "cases": cases,
            "case_history": history,
        }
