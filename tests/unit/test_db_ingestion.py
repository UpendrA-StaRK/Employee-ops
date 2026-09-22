"""Unit tests for PostgreSQL source ingestion.

Strategy:
- The source_departments table is created ONCE per test session using a
  separate committed transaction (not the rolling-back db_session fixture),
  because ingest_postgres opens its own engine/connection and cannot see
  data that hasn't been committed by the test fixture connection.
- The bad-connection tests use a clearly invalid host name that will never
  resolve, avoiding dependency on real credentials.
- All data inserted for tests is cleaned up in the session-scoped teardown.
"""
import pytest
from sqlalchemy import create_engine, text

from app.pipelines.db_ingestion import ingest_postgres

# ── Session-scoped source table setup ────────────────────────────────────────

@pytest.fixture(scope="session")
def pg_source_table():
    """Create source_departments in the TEST database with committed data.

    We must COMMIT here because ingest_postgres opens its own engine and
    can only see committed rows. Using the rolling-back db_session fixture
    would make the table invisible to ingest_postgres.
    """
    from tests.conftest import TEST_DATABASE_URL

    engine = create_engine(TEST_DATABASE_URL)
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS source_departments"))
        conn.execute(text("""
            CREATE TABLE source_departments (
                code   VARCHAR(20) PRIMARY KEY,
                name   VARCHAR(100) NOT NULL
            )
        """))
        conn.execute(text("""
            INSERT INTO source_departments (code, name) VALUES
                ('HR',  'Human Resources'),
                ('ENG', 'Engineering'),
                ('FIN', 'Finance')
        """))
    # engine.begin() auto-commits on exit

    yield TEST_DATABASE_URL

    # Teardown: drop the source table
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS source_departments"))
    engine.dispose()


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestPostgresIngestionSuccess:
    """Happy-path: reading from an accessible source table."""

    def test_returns_list_of_dicts(self, pg_source_table):
        data = ingest_postgres("SELECT * FROM source_departments", pg_source_table)
        assert isinstance(data, list)
        assert len(data) == 3

    def test_dict_keys_match_column_names(self, pg_source_table):
        data = ingest_postgres("SELECT * FROM source_departments", pg_source_table)
        assert set(data[0].keys()) == {"code", "name"}

    def test_correct_values_returned(self, pg_source_table):
        data = ingest_postgres(
            "SELECT * FROM source_departments ORDER BY code", pg_source_table
        )
        codes = [r["code"] for r in data]
        assert "HR" in codes
        assert "ENG" in codes

    def test_filtered_query(self, pg_source_table):
        """Ingestion supports arbitrary SELECT queries including WHERE clauses."""
        data = ingest_postgres(
            "SELECT * FROM source_departments WHERE code = 'HR'", pg_source_table
        )
        assert len(data) == 1
        assert data[0]["name"] == "Human Resources"

    def test_empty_result(self, pg_source_table):
        """An empty result set is returned as an empty list, not an error."""
        data = ingest_postgres(
            "SELECT * FROM source_departments WHERE code = 'DOES_NOT_EXIST'",
            pg_source_table,
        )
        assert data == []

    def test_does_not_modify_source(self, pg_source_table):
        """Running ingestion must not alter source data."""
        before = ingest_postgres(
            "SELECT count(*) AS n FROM source_departments", pg_source_table
        )
        # Run ingestion a second time
        ingest_postgres("SELECT * FROM source_departments", pg_source_table)
        after = ingest_postgres(
            "SELECT count(*) AS n FROM source_departments", pg_source_table
        )
        assert before[0]["n"] == after[0]["n"]


class TestPostgresIngestionConnectionFailure:
    """Verify that connection failures are surfaced as ConnectionError."""

    def test_bad_host_raises_connection_error(self):
        bad_url = "postgresql+psycopg://user:pass@nonexistent_host_xyz_99999:5432/db"
        with pytest.raises(ConnectionError):
            ingest_postgres("SELECT 1", bad_url)


class TestPostgresIngestionQueryFailure:
    """Verify that query failures are surfaced as RuntimeError."""

    def test_missing_table_raises_runtime_error(self, pg_source_table):
        with pytest.raises(RuntimeError):
            ingest_postgres("SELECT * FROM nonexistent_table_xyz", pg_source_table)

    def test_invalid_sql_raises_runtime_error(self, pg_source_table):
        with pytest.raises(RuntimeError):
            ingest_postgres("NOT VALID SQL AT ALL", pg_source_table)
