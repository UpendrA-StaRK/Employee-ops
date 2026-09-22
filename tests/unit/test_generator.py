"""Unit tests for the synthetic data generator.

These tests run entirely in memory and do not require a database.
"""
import pytest

from generators.generator import SyntheticDataGenerator, ALLOWED_TRANSITIONS


def test_generator_reproducibility():
    """Identical seeds should produce identical output."""
    gen1 = SyntheticDataGenerator(seed=123)
    dataset1 = gen1.generate(n_employees=10, n_cases=20, scenario="clean")

    gen2 = SyntheticDataGenerator(seed=123)
    dataset2 = gen2.generate(n_employees=10, n_cases=20, scenario="clean")

    assert dataset1 == dataset2


def test_generator_diversity():
    """Different seeds should produce different output."""
    gen1 = SyntheticDataGenerator(seed=1)
    dataset1 = gen1.generate(n_employees=10, n_cases=10, scenario="clean")

    gen2 = SyntheticDataGenerator(seed=2)
    dataset2 = gen2.generate(n_employees=10, n_cases=10, scenario="clean")

    # Just asserting the first employee's ID is different is enough to prove diversity
    assert dataset1["employees"][0]["employee_id"] != dataset2["employees"][0]["employee_id"]


def test_generator_counts():
    """The generator should respect the requested counts."""
    gen = SyntheticDataGenerator(seed=42)
    dataset = gen.generate(n_employees=5, n_cases=12, scenario="clean")

    assert len(dataset["employees"]) == 5
    assert len(dataset["cases"]) == 12
    # Case history will have at least 1 per case, usually more
    assert len(dataset["case_history"]) >= 12


def test_clean_scenario_relationships():
    """Clean scenario should have valid foreign key relationships."""
    gen = SyntheticDataGenerator(seed=42)
    dataset = gen.generate(n_employees=20, n_cases=50, scenario="clean")

    employee_ids = {e["employee_id"] for e in dataset["employees"]}
    case_ids = {c["case_id"] for c in dataset["cases"]}

    # All cases must reference a valid employee
    for case in dataset["cases"]:
        assert case["employee_id"] in employee_ids

    # All history must reference a valid case
    for history in dataset["case_history"]:
        assert history["case_id"] in case_ids


def test_clean_scenario_lifecycle():
    """Clean scenario history must follow allowed transitions and be chronological."""
    gen = SyntheticDataGenerator(seed=42)
    dataset = gen.generate(n_employees=10, n_cases=20, scenario="clean")

    # Group history by case
    history_by_case = {}
    for h in dataset["case_history"]:
        history_by_case.setdefault(h["case_id"], []).append(h)

    for case in dataset["cases"]:
        history = history_by_case[case["case_id"]]
        
        # Must have at least the creation record
        assert len(history) > 0
        assert history[0]["old_status"] is None
        assert history[0]["new_status"] == "OPEN"

        # Check chronology and transitions
        for i in range(1, len(history)):
            prev = history[i - 1]
            curr = history[i]
            
            # Transition must be valid
            assert curr["new_status"] in ALLOWED_TRANSITIONS[prev["new_status"]]
            # Chronological
            assert curr["created_at"] >= prev["created_at"]

        # Terminal status of case must match the final history record
        assert case["status"] == history[-1]["new_status"]


def test_duplicates_scenario():
    """Duplicates scenario should introduce duplicate employee and case records."""
    gen = SyntheticDataGenerator(seed=42)
    dataset = gen.generate(n_employees=100, n_cases=200, scenario="duplicates")

    assert len(dataset["employees"]) > 100
    assert len(dataset["cases"]) > 200

    # There should be duplicate employee IDs
    emp_ids = [e["employee_id"] for e in dataset["employees"]]
    assert len(emp_ids) > len(set(emp_ids))


def test_missing_fields_scenario():
    """Missing fields scenario should introduce None values."""
    gen = SyntheticDataGenerator(seed=42)
    dataset = gen.generate(n_employees=100, n_cases=200, scenario="missing_fields")

    missing_emp = sum(1 for e in dataset["employees"] if not all(e.values()))
    assert missing_emp > 0

    missing_cases = sum(1 for c in dataset["cases"] if not all(c.values()))
    assert missing_cases > 0


def test_invalid_values_scenario():
    """Invalid values scenario should introduce malformed data."""
    gen = SyntheticDataGenerator(seed=42)
    dataset = gen.generate(n_employees=50, n_cases=100, scenario="invalid_values")

    invalid_emails = [e for e in dataset["employees"] if e["email"] == "NOT_AN_EMAIL"]
    invalid_statuses = [e for e in dataset["employees"] if e["status"] == "ZOMBIE"]
    invalid_dates = [e for e in dataset["employees"] if e["created_at"] == "not-a-date"]

    assert any((invalid_emails, invalid_statuses, invalid_dates))

    invalid_case_statuses = [c for c in dataset["cases"] if c["status"] == "FLYING"]
    invalid_priorities = [c for c in dataset["cases"] if c["priority"] == "SUPER_DUPER_URGENT"]
    invalid_categories = [c for c in dataset["cases"] if c["category"] == "MADE_UP"]
    
    assert any((invalid_case_statuses, invalid_priorities, invalid_categories))

    invalid_history = [h for h in dataset["case_history"] if h["new_status"] == "INVALID_STATE"]
    assert len(invalid_history) > 0


def test_orphan_records_scenario():
    """Orphan records scenario should introduce broken foreign keys."""
    gen = SyntheticDataGenerator(seed=42)
    dataset = gen.generate(n_employees=50, n_cases=100, scenario="orphan_records")

    emp_ids = {e["employee_id"] for e in dataset["employees"]}
    case_ids = {c["case_id"] for c in dataset["cases"]}

    orphaned_cases = [c for c in dataset["cases"] if c["employee_id"] not in emp_ids]
    assert len(orphaned_cases) > 0

    orphaned_history = [h for h in dataset["case_history"] if h["case_id"] not in case_ids]
    assert len(orphaned_history) > 0


# ---------------------------------------------------------------------------
# Week 2 Part 1: Parquet export tests
# ---------------------------------------------------------------------------

def test_write_parquet_clean(tmp_path):
    """_write_parquet should produce a readable Parquet file with correct row count."""
    import pyarrow.parquet as pq
    from generators.generate import _write_parquet

    gen = SyntheticDataGenerator(seed=42)
    dataset = gen.generate(n_employees=10, n_cases=20, scenario="clean")
    employees = dataset["employees"]

    out = tmp_path / "employees.parquet"
    _write_parquet(out, employees)

    assert out.exists(), "Parquet file should be created"
    table = pq.read_table(str(out))
    assert table.num_rows == len(employees), "Row count must match"
    # All canonical employee fields must be present as columns
    expected_columns = {"employee_id", "name", "email", "department", "job_title", "status", "created_at", "updated_at"}
    assert expected_columns.issubset(set(table.schema.names))


def test_write_parquet_missing_fields_scenario(tmp_path):
    """Parquet writer must preserve None values from the missing_fields scenario."""
    import pyarrow.parquet as pq
    from generators.generate import _write_parquet

    gen = SyntheticDataGenerator(seed=42)
    dataset = gen.generate(n_employees=50, n_cases=100, scenario="missing_fields")
    employees = dataset["employees"]

    out = tmp_path / "employees_missing.parquet"
    _write_parquet(out, employees)

    table = pq.read_table(str(out))
    # The missing_fields scenario introduces None values; at least one null must survive
    null_counts = {col: table.column(col).null_count for col in table.schema.names}
    total_nulls = sum(null_counts.values())
    assert total_nulls > 0, "Missing-fields scenario nulls must round-trip through Parquet"


def test_cli_parquet_format(tmp_path):
    """CLI --format parquet should write .parquet files and no .csv/.json files."""
    from generators.generate import main

    ret = main([
        "--employees", "10",
        "--cases", "20",
        "--scenario", "clean",
        "--seed", "42",
        "--format", "parquet",
        "--output-dir", str(tmp_path),
    ])
    assert ret == 0

    for name in ("employees", "cases", "case_history"):
        parquet_file = tmp_path / f"{name}.parquet"
        assert parquet_file.exists(), f"{name}.parquet should exist"
        # CSV and JSON must NOT be written for --format parquet
        assert not (tmp_path / f"{name}.csv").exists(), f"{name}.csv must not be written"
        assert not (tmp_path / f"{name}.json").exists(), f"{name}.json must not be written"


def test_cli_all_format_writes_all_three(tmp_path):
    """CLI --format all should write csv, json, and parquet for every dataset."""
    from generators.generate import main

    ret = main([
        "--employees", "10",
        "--cases", "20",
        "--scenario", "clean",
        "--seed", "42",
        "--format", "all",
        "--output-dir", str(tmp_path),
    ])
    assert ret == 0

    for name in ("employees", "cases", "case_history"):
        for ext in (".csv", ".json", ".parquet"):
            assert (tmp_path / f"{name}{ext}").exists(), f"{name}{ext} must be written by --format all"


def test_parquet_deterministic(tmp_path):
    """Parquet output must be deterministic: same seed → identical row count and values."""
    import pyarrow.parquet as pq
    from generators.generate import _write_parquet

    gen_a = SyntheticDataGenerator(seed=99)
    gen_b = SyntheticDataGenerator(seed=99)
    employees_a = gen_a.generate(n_employees=15, n_cases=30, scenario="clean")["employees"]
    employees_b = gen_b.generate(n_employees=15, n_cases=30, scenario="clean")["employees"]

    out_a = tmp_path / "emp_a.parquet"
    out_b = tmp_path / "emp_b.parquet"
    _write_parquet(out_a, employees_a)
    _write_parquet(out_b, employees_b)

    table_a = pq.read_table(str(out_a))
    table_b = pq.read_table(str(out_b))

    assert table_a.num_rows == table_b.num_rows
    # Compare first employee_id column to confirm identical values
    assert table_a.column("employee_id").to_pylist() == table_b.column("employee_id").to_pylist()
