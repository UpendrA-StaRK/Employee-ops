"""File ingestion layer for the Enterprise Data Pipeline.

This module is responsible for reading raw source files (CSV, JSON, Parquet)
into a predictable in-memory representation (a list of dictionaries).

It is strictly an ingestion abstraction. It does NOT perform:
- Schema validation
- Data quality checks
- Business logic transformations
"""
import csv
import json
from pathlib import Path
from typing import Any


def ingest_csv(path: Path) -> list[dict[str, Any]]:
    """Ingest a CSV file into a list of dictionaries.

    Args:
        path: Path to the CSV file.

    Returns:
        List of dictionaries where keys are column headers.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not path.exists():
        raise FileNotFoundError(f"Source file not found: {path}")

    # Read the file
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # Empty CSV with no headers yields empty list.
        # Empty CSV with headers yields empty list.
        if reader.fieldnames is None:
            return []
        
        return list(reader)


def ingest_json(path: Path) -> list[dict[str, Any]]:
    """Ingest a JSON file into a list of dictionaries.

    Args:
        path: Path to the JSON file. Expects a JSON array of objects.

    Returns:
        List of dictionaries.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
        ValueError: If the root JSON element is not a list.
    """
    if not path.exists():
        raise FileNotFoundError(f"Source file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        # Load the content
        # This will raise JSONDecodeError for empty or malformed files
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON array, got {type(data).__name__} in {path}")

    return data


def ingest_parquet(path: Path) -> list[dict[str, Any]]:
    """Ingest a Parquet file into a list of dictionaries.

    Args:
        path: Path to the Parquet file.

    Returns:
        List of dictionaries representing the rows.

    Raises:
        FileNotFoundError: If the file does not exist.
        ImportError: If pyarrow is not installed.
        ValueError: If the file is corrupt or unreadable.
    """
    if not path.exists():
        raise FileNotFoundError(f"Source file not found: {path}")

    try:
        import pyarrow.parquet as pq
        import pyarrow.lib as pa_lib
    except ImportError as e:
        raise ImportError("pyarrow is required for Parquet ingestion") from e

    try:
        table = pq.read_table(str(path))
        return table.to_pylist()
    except pa_lib.ArrowInvalid as e:
        raise ValueError(f"Failed to read Parquet file {path}: {e}") from e


def ingest_file(path: Path) -> list[dict[str, Any]]:
    """Dynamically ingest a file based on its extension.

    Supported extensions: .csv, .json, .parquet

    Args:
        path: Path to the source file.

    Returns:
        List of dictionaries representing the ingested records.

    Raises:
        ValueError: If the file extension is unsupported.
        FileNotFoundError: If the file does not exist.
    """
    if not path.exists():
        raise FileNotFoundError(f"Source file not found: {path}")

    ext = path.suffix.lower()
    if ext == ".csv":
        return ingest_csv(path)
    elif ext == ".json":
        return ingest_json(path)
    elif ext == ".parquet":
        return ingest_parquet(path)
    else:
        raise ValueError(f"Unsupported file format: {ext}")


def ingest_dataframe(path: Path) -> Any:
    """Dynamically ingest a file into a Pandas DataFrame based on its extension.

    This wraps `ingest_file` to guarantee identical parsing rules (e.g., preservation 
    of strings and nulls), converting the resulting list of dictionaries into a DataFrame.

    Args:
        path: Path to the source file.

    Returns:
        Pandas DataFrame representing the ingested records.

    Raises:
        ValueError: If the file extension is unsupported.
        FileNotFoundError: If the file does not exist.
        ImportError: If pandas is not installed.
    """
    try:
        import pandas as pd
    except ImportError as e:
        raise ImportError("pandas is required for DataFrame ingestion") from e
    
    data = ingest_file(path)
    return pd.DataFrame(data)
