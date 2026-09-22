"""Unit tests for the File Ingestion layer."""
import json
import pytest
from pathlib import Path

from app.pipelines.ingestion import ingest_csv, ingest_json, ingest_parquet, ingest_file

# We can rely on PyArrow being available since it was added in pyproject.toml
import pyarrow as pa
import pyarrow.parquet as pq


def test_ingest_csv_success(tmp_path: Path):
    """Test successful ingestion of a CSV file."""
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("id,name,dept\n1,Alice,HR\n2,,Finance", encoding="utf-8")

    data = ingest_csv(csv_path)
    assert len(data) == 2
    assert data[0] == {"id": "1", "name": "Alice", "dept": "HR"}
    # Note that empty string is preserved, we don't apply business logic to change it to None
    assert data[1] == {"id": "2", "name": "", "dept": "Finance"}


def test_ingest_csv_empty(tmp_path: Path):
    """Test reading an entirely empty CSV file (no headers)."""
    csv_path = tmp_path / "empty.csv"
    csv_path.write_text("", encoding="utf-8")

    data = ingest_csv(csv_path)
    assert data == []


def test_ingest_json_success(tmp_path: Path):
    """Test successful ingestion of a JSON file."""
    json_path = tmp_path / "data.json"
    content = [{"id": 1, "name": "Alice"}, {"id": 2, "name": None}]
    json_path.write_text(json.dumps(content), encoding="utf-8")

    data = ingest_json(json_path)
    assert len(data) == 2
    assert data[0]["name"] == "Alice"
    assert data[1]["name"] is None


def test_ingest_json_invalid(tmp_path: Path):
    """Test handling of invalid JSON content."""
    json_path = tmp_path / "bad.json"
    json_path.write_text("{not valid json", encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        ingest_json(json_path)


def test_ingest_json_not_array(tmp_path: Path):
    """Test handling of valid JSON that isn't a list/array."""
    json_path = tmp_path / "obj.json"
    json_path.write_text('{"id": 1}', encoding="utf-8")

    with pytest.raises(ValueError, match="Expected a JSON array"):
        ingest_json(json_path)


def test_ingest_parquet_success(tmp_path: Path):
    """Test successful ingestion of a Parquet file."""
    parquet_path = tmp_path / "data.parquet"
    
    # Create a small parquet file using PyArrow
    schema = pa.schema([("id", pa.int64()), ("name", pa.string())])
    table = pa.Table.from_arrays([
        pa.array([1, 2]),
        pa.array(["Alice", None])
    ], schema=schema)
    pq.write_table(table, str(parquet_path))

    data = ingest_parquet(parquet_path)
    assert len(data) == 2
    assert data[0] == {"id": 1, "name": "Alice"}
    assert data[1] == {"id": 2, "name": None}


def test_ingest_parquet_corrupt(tmp_path: Path):
    """Test handling of a corrupt Parquet file."""
    parquet_path = tmp_path / "corrupt.parquet"
    parquet_path.write_bytes(b"not a parquet file")

    with pytest.raises(ValueError, match="Failed to read Parquet file"):
        ingest_parquet(parquet_path)


def test_file_not_found():
    """All readers should raise FileNotFoundError for missing files."""
    missing = Path("does_not_exist.csv")
    with pytest.raises(FileNotFoundError):
        ingest_csv(missing)
    with pytest.raises(FileNotFoundError):
        ingest_json(missing)
    with pytest.raises(FileNotFoundError):
        ingest_parquet(missing)
    with pytest.raises(FileNotFoundError):
        ingest_file(missing)


def test_ingest_file_routing(tmp_path: Path):
    """Test the dynamic routing based on extension."""
    csv_path = tmp_path / "test.csv"
    csv_path.write_text("a\n1", encoding="utf-8")
    
    assert len(ingest_file(csv_path)) == 1

    txt_path = tmp_path / "test.txt"
    txt_path.write_text("dummy", encoding="utf-8")
    with pytest.raises(ValueError, match="Unsupported file format"):
        ingest_file(txt_path)


def test_ingest_dataframe(tmp_path: Path):
    """Test that ingest_dataframe returns a Pandas DataFrame."""
    from app.pipelines.ingestion import ingest_dataframe
    import pandas as pd

    csv_path = tmp_path / "df_test.csv"
    csv_path.write_text("id,val\n1,A\n2,B", encoding="utf-8")
    
    df = ingest_dataframe(csv_path)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert list(df.columns) == ["id", "val"]
    assert df.iloc[0]["id"] == "1"
