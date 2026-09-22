"""Unit tests for PySpark Analytics (Part 10).

These tests use a local SparkSession to verify the execution of our
transformations, joins, and aggregations without needing a real cluster.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from pyspark.sql import DataFrame, Row, SparkSession

from app.pipelines.spark_analytics import (
    aggregate_by_department,
    create_spark_session,
    perform_join,
    transform_and_enrich,
)


@pytest.fixture(scope="module")
def spark() -> SparkSession:
    """Provide a module-level SparkSession for tests to minimize JVM startup overhead."""
    session = create_spark_session("Test_EmployeeOps_Analytics")
    yield session
    session.stop()


@pytest.fixture
def mock_cases_df(spark: SparkSession) -> DataFrame:
    """Deterministic, small dataset mimicking raw cases."""
    data = [
        Row(case_id="c1", employee_id="e1", case_type="Grievance", priority="High", status="Open"),
        Row(case_id="c2", employee_id="e2", case_type="Inquiry", priority="Low", status="Closed"),
        Row(case_id="c3", employee_id="e1", case_type="Inquiry", priority="Medium", status="Pending"),
        Row(case_id="c4", employee_id="e99", case_type="Grievance", priority="High", status="Open"), # e99 has no employee record
        Row(case_id="c5", employee_id="e3", case_type="Payroll", priority=None, status=None), # Malformed/null status
    ]
    return spark.createDataFrame(data)


@pytest.fixture
def mock_employees_df(spark: SparkSession) -> DataFrame:
    """Deterministic, small dataset mimicking raw employees."""
    data = [
        Row(employee_id="e1", name="Alice", department="Engineering", job_title="Dev"),
        Row(employee_id="e2", name="Bob", department="HR", job_title="Manager"),
        Row(employee_id="e3", name="Charlie", department="Engineering", job_title="QA"),
    ]
    return spark.createDataFrame(data)


def test_transform_and_enrich(mock_cases_df: DataFrame):
    """Test filtering logic, null handling, and derived column creation."""
    result_df = transform_and_enrich(mock_cases_df)
    
    # Action: collect to local Python list for assertion
    results = result_df.collect()
    
    # Should exclude c2 (Closed) and c5 (null status)
    assert len(results) == 3
    
    # Check derived column 'is_high_priority'
    c1 = next(row for row in results if row.case_id == "c1")
    assert c1.is_high_priority is True
    
    c3 = next(row for row in results if row.case_id == "c3")
    assert c3.is_high_priority is False


def test_perform_join_maintains_grain_and_handles_unmatched(mock_cases_df: DataFrame, mock_employees_df: DataFrame):
    """Test that left join preserves all cases and fills unmatched departments."""
    # First, transform
    enriched_cases = transform_and_enrich(mock_cases_df)
    
    # Perform join
    joined_df = perform_join(enriched_cases, mock_employees_df)
    results = joined_df.collect()
    
    # Grain check: We started with 3 enriched cases, we must end with 3.
    assert len(results) == 3
    
    # Check matched record
    c1 = next(row for row in results if row.case_id == "c1")
    assert c1.department == "Engineering"
    
    # Check unmatched record (c4 belongs to e99 which isn't in employees_df)
    # The null department should be filled with "UNKNOWN_DEPT"
    c4 = next(row for row in results if row.case_id == "c4")
    assert c4.department == "UNKNOWN_DEPT"


def test_aggregate_by_department(mock_cases_df: DataFrame, mock_employees_df: DataFrame):
    """Test the final aggregation logic (grain change)."""
    enriched_cases = transform_and_enrich(mock_cases_df)
    joined_df = perform_join(enriched_cases, mock_employees_df)
    
    # Aggregation
    agg_df = aggregate_by_department(joined_df)
    results = agg_df.collect()
    
    # We expect 2 groups: "Engineering" (e1's cases) and "UNKNOWN_DEPT" (e99's cases)
    # c3 also belongs to e1 (Engineering).
    # Total Engineering active cases = c1 (High) + c3 (Not High) = 2
    # Total Unknown active cases = c4 (High) = 1
    
    assert len(results) == 2
    
    eng_row = next(row for row in results if row.department == "Engineering")
    assert eng_row.active_cases_count == 2
    assert eng_row.high_priority_count == 1
    
    unk_row = next(row for row in results if row.department == "UNKNOWN_DEPT")
    assert unk_row.active_cases_count == 1
    assert unk_row.high_priority_count == 1
