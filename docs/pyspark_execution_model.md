# PySpark Integration & Execution Model (Part 10)

## 1. Architectural Boundary: PySpark vs Existing Pipeline

It is critical to understand that **Spark is an execution technology, not a new logical business stage.**

Our existing logical data pipeline looks like this:
```
RAW → STANDARDIZE → VALID → JOIN → CURATED → AGGREGATION
```

**Existing Python Implementation:**
In the existing codebase (Parts 1-9), this logical flow is executed in a single Python process. We use `list[dict]`, simple pure functions for filtering, and SQLAlchemy for persistence. 

**PySpark Implementation:**
The Spark implementation (`app/pipelines/spark_analytics.py`) does **not** replace our ingestion system, standardizer, validation, or PostgreSQL database. Instead, it demonstrates how those same logical transformations (filtering, joining, aggregating) can be expressed using Spark DataFrames so that execution can be distributed across many nodes in a cluster.

Spark becomes necessary when data volume or velocity exceeds what a single Python process can handle comfortably in memory. **Spark does not automatically make the pipeline "better";** it adds operational complexity in exchange for horizontal scalability.

---

## 2. Explicit Spark Schemas

In `spark_analytics.py`, we explicitly define `StructType` schemas for our Employee and Case datasets before reading them.

While Spark *can* infer schemas (e.g., `inferSchema=True` for JSON or CSV), doing so requires Spark to read the entire dataset first, which is expensive. More importantly, inference can guess incorrectly (e.g., inferring a string ID as an integer if it happens to only contain numbers). 

**Data Contracts:** Explicit schemas enforce our data contracts at the boundary where Spark reads the data.

*Note on Data Formats:* The script natively reads the generated `Parquet` files because Parquet is a columnar format optimized for Spark. However, Spark can read the generated `JSON` or `CSV` files just as easily simply by changing the `format_type` parameter in the `load_data` function.

---

## 3. Lazy Evaluation: Transformations vs Actions

Spark defers execution until absolutely necessary. This concept is called **Lazy Evaluation**.

### Transformations
Operations like `select()`, `filter()`, `withColumn()`, `join()`, and `groupBy()` are **Transformations**. 
When you call them, Spark does not process any data. Instead, it builds a Logical Execution Plan (a DAG - Directed Acyclic Graph) representing the steps to take.

### Actions
Operations like `show()`, `count()`, `collect()`, and `write()` are **Actions**. 
When an action is called, Spark optimizes the logical plan into a Physical Plan and finally executes the computations across the cluster.

---

## 4. Partitions and Shuffles

**Partitions:** 
Spark divides large datasets into smaller chunks called partitions. Each partition is processed in parallel by a different core or node. 

**Shuffles:**
Some operations require Spark to move data across the network between nodes to ensure related data is co-located. This data movement is called a **Shuffle**.

- **Joins:** When we join Cases and Employees on `employee_id`, Spark must shuffle the data so that a Case and its corresponding Employee end up on the same physical node to be joined.
- **Aggregations:** When we `groupBy("department")`, Spark must shuffle all records belonging to "Engineering" to the same node to count them accurately.

*Shuffles are the most expensive operation in distributed processing.* In our script, we keep `spark.sql.shuffle.partitions` small (e.g., 4) because we are running locally on small datasets, preventing Spark from creating 200 tiny partitions (its default).

---

## 5. Handling Nulls Deliberately

Distributed processing often exposes messy data. We deliberately handle nulls using Spark's API:
- `filter(F.col("status").isNotNull())`: Explicitly dropping malformed rows rather than assuming Python `None` truthiness.
- `fillna({"department": "UNKNOWN_DEPT"})`: Safely coalescing unmatched outer/left join results instead of silently passing nulls downstream.

---

## 6. Deterministic Output and Idempotency

Just as in Part 9, our Spark script writes output deterministically using `.write.mode("overwrite")`. Running the script multiple times against the same generated input will yield the exact same aggregated JSON summary without duplicating rows.
