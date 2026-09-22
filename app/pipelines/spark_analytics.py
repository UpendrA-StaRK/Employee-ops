"""PySpark Integration / Execution Model (Part 10).

This module demonstrates PySpark as an execution engine, focusing on
distributed data processing concepts. It is an educational component and does NOT
replace the existing Python/pandas/SQL business pipeline (RAW -> STANDARDIZE ->
VALID -> JOIN -> CURATED -> AGGREGATION).

Concepts Demonstrated:
    1. SparkSession creation (local mode).
    2. Explicit Schemas: Defining StructTypes rather than relying on inference.
    3. Lazy Evaluation: Transformations (select, filter) vs Actions (count, write).
    4. DataFrames: Using Spark's DataFrame API for manipulation.
    5. Joins: Combining datasets and handling cardinality.
    6. Aggregations: groupBy and agg to change the grain of the data.
    7. Partitions & Shuffle: Understanding when data moves across nodes.
    8. Null Handling: Safely handling missing values in Spark.
"""
from __future__ import annotations

import logging
from pathlib import Path

from pyspark.sql import DataFrame, SparkSession
import pyspark.sql.functions as F
from pyspark.sql.types import (
    BooleanType,
    IntegerType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

import sys
import os

logger = logging.getLogger(__name__)


def create_spark_session(app_name: str = "EmployeeOps_Analytics") -> SparkSession:
    """Create and configure a local SparkSession.

    In a production environment, this would be configured to connect to a
    cluster (e.g., YARN, Kubernetes, Databricks). For this local demonstration,
    we use 'local[*]' to use all available local cores.

    Args:
        app_name: The name of the Spark application.

    Returns:
        An active SparkSession.
    """
    os.environ["PYSPARK_PYTHON"] = sys.executable
    os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable
    logger.info("Initializing local SparkSession: %s", app_name)
    spark = (
        SparkSession.builder.appName(app_name)
        .master("local[*]")
        # Avoid generating too many shuffle partitions for small local datasets
        .config("spark.sql.shuffle.partitions", "4")
        # Suppress verbose Spark logging in the console
        .config("spark.driver.extraJavaOptions", "-Dlog4j.level=WARN")
        .getOrCreate()
    )
    # Set log level programmatically to avoid console spam
    spark.sparkContext.setLogLevel("WARN")
    return spark


def define_schemas() -> tuple[StructType, StructType]:
    """Define explicit Spark SQL schemas for the generated data.

    Why explicit schemas?
    Relying on Spark's automatic schema inference (e.g., inferSchema=True for CSV/JSON)
    requires an extra pass over the data and can lead to incorrect types if the
    sample data is ambiguous. Defining explicit schemas ensures data contract
    enforcement at the execution boundary.

    Returns:
        A tuple of (employee_schema, case_schema).
    """
    employee_schema = StructType([
        StructField("employee_id", StringType(), False),
        StructField("name", StringType(), True),
        StructField("email", StringType(), True),
        StructField("department", StringType(), True),
        StructField("job_title", StringType(), True),
        StructField("status", StringType(), True),
        StructField("created_at", StringType(), True),  # Read as string, cast later if needed
        StructField("updated_at", StringType(), True),
    ])

    case_schema = StructType([
        StructField("case_id", StringType(), False),
        StructField("employee_id", StringType(), True),
        StructField("case_type", StringType(), True),
        StructField("priority", StringType(), True),
        StructField("status", StringType(), True),
        StructField("created_at", StringType(), True),
        StructField("updated_at", StringType(), True),
    ])

    return employee_schema, case_schema


def load_data(
    spark: SparkSession,
    data_dir: Path,
    format_type: str = "parquet"
) -> tuple[DataFrame, DataFrame]:
    """Load generated datasets into Spark DataFrames.

    Spark can natively read Parquet, JSON, and CSV. We use Parquet here as it is
    columnar, heavily optimized for analytical reads, and natively preserves types.
    However, you could easily change `format_type="json"` and point to the JSON outputs.

    Args:
        spark: Active SparkSession.
        data_dir: Path to the generated data directory.
        format_type: Format to read ("parquet", "json", "csv").

    Returns:
        Tuple of (employees_df, cases_df).
    """
    employee_schema, case_schema = define_schemas()

    employees_path = str(data_dir / f"employees.{format_type}")
    cases_path = str(data_dir / f"cases.{format_type}")

    logger.info("Loading %s data from %s", format_type, employees_path)

    # Parquet preserves its own schema, so we don't strictly *need* to supply ours,
    # but we do so here to demonstrate explicit schema enforcement.
    employees_df = spark.read.format(format_type).schema(employee_schema).load(employees_path)
    cases_df = spark.read.format(format_type).schema(case_schema).load(cases_path)

    return employees_df, cases_df


def transform_and_enrich(cases_df: DataFrame) -> DataFrame:
    """Demonstrate lazy transformations: select, filter, withColumn.

    All operations here are TRANSFORMATIONS. They do not execute immediately.
    Spark builds a logical plan and only executes it when an ACTION (like count or write)
    is triggered.

    Args:
        cases_df: Raw cases DataFrame.

    Returns:
        Enriched cases DataFrame.
    """
    # 1. Select: Prune unnecessary columns early (good practice)
    pruned_df = cases_df.select(
        "case_id", "employee_id", "case_type", "priority", "status"
    )

    # 2. Filter: Keep only cases that are not strictly 'Closed'
    # Null handling: F.col("status").isNotNull() is deliberate defensive programming.
    active_df = pruned_df.filter(
        F.col("status").isNotNull() & (F.col("status") != "Closed")
    )

    # 3. withColumn: Derive a new field based on priority
    # Demonstrates conditional logic (when/otherwise) in Spark SQL expressions.
    enriched_df = active_df.withColumn(
        "is_high_priority",
        F.when(F.col("priority") == "High", F.lit(True)).otherwise(F.lit(False))
    )

    return enriched_df


def perform_join(enriched_cases_df: DataFrame, employees_df: DataFrame) -> DataFrame:
    """Demonstrate joining DataFrames and shuffle awareness.

    Join characteristics:
        - Key: 'employee_id'
        - Type: 'left' (Keep all active cases, even if employee is missing)
        - Cardinality: Many Cases to One Employee
        - Grain: Output remains 1 row per Case

    Shuffle Implication:
        Joining requires Spark to physically move data across the network
        so that records with the same 'employee_id' end up on the same node
        (a "Shuffle"). Shuffles are the most expensive operation in distributed computing.

    Args:
        enriched_cases_df: Transformed cases DataFrame.
        employees_df: Raw employees DataFrame.

    Returns:
        Joined DataFrame.
    """
    # Select only what we need from employees to avoid wide, bloated rows
    emp_subset = employees_df.select("employee_id", "department", "job_title")

    # Left join to preserve all cases.
    joined_df = enriched_cases_df.join(
        emp_subset,
        on="employee_id",
        how="left"
    )

    # Handle nulls resulting from the left join (if employee is missing)
    safe_joined_df = joined_df.fillna({
        "department": "UNKNOWN_DEPT",
        "job_title": "UNKNOWN_TITLE"
    })

    return safe_joined_df


def aggregate_by_department(joined_df: DataFrame) -> DataFrame:
    """Demonstrate aggregations to change the data grain.

    Aggregation changes the grain:
        - Input grain: 1 row per Case
        - Output grain: 1 row per Department

    Shuffle Implication:
        Like joins, groupBy requires a shuffle. All records for "Engineering"
        must be moved to the same executor to be counted.

    Args:
        joined_df: The joined Cases + Employees DataFrame.

    Returns:
        Aggregated DataFrame.
    """
    agg_df = joined_df.groupBy("department").agg(
        F.count("case_id").alias("active_cases_count"),
        F.sum(F.col("is_high_priority").cast(IntegerType())).alias("high_priority_count")
    )

    # Sort the result deterministically
    return agg_df.orderBy(F.desc("active_cases_count"), "department")


def write_output(df: DataFrame, output_path: Path) -> None:
    """Demonstrate an Action: Writing data.

    This is an ACTION. Calling .write triggers the lazy evaluation of all
    preceding transformations (select, filter, withColumn, join, groupBy).

    Args:
        df: The final DataFrame to write.
        output_path: Where to save the result.
    """
    out_dir = str(output_path)
    logger.info("Writing aggregated result to %s", out_dir)

    # We use coalesce(1) here purely for demonstration/local testing, to produce
    # a single output file. In a real cluster, you would let Spark write multiple
    # partitioned files for parallel throughput.
    df.coalesce(1).write.mode("overwrite").format("json").save(out_dir)


def run_spark_analytics(data_dir: Path, output_dir: Path) -> None:
    """Orchestrate the local Spark execution pipeline."""
    spark = create_spark_session()
    try:
        # Load
        employees_df, cases_df = load_data(spark, data_dir, format_type="parquet")

        # Transform
        enriched_cases = transform_and_enrich(cases_df)

        # Join
        joined_data = perform_join(enriched_cases, employees_df)

        # Aggregation (Change of grain)
        department_summary = aggregate_by_department(joined_data)

        # Action: Trigger execution and output
        # Also print to console for local inspection
        logger.info("Department Summary (Action: show):")
        department_summary.show(truncate=False)

        write_output(department_summary, output_dir)

    finally:
        logger.info("Stopping SparkSession")
        spark.stop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    base_dir = Path(__file__).resolve().parents[2]
    run_spark_analytics(
        data_dir=base_dir / "data" / "generated",
        output_dir=base_dir / "data" / "spark_output" / "cases_by_department"
    )
