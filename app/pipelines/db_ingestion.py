"""PostgreSQL source ingestion for the Enterprise Data Pipeline.

This module reads source data from a PostgreSQL database using raw
read-only SQL queries. It does NOT perform business validation or
transformation — that is the responsibility of later pipeline stages.

Design note: PostgreSQL serves a dual role in this project:
  - Week 1: application database (employees, cases, case_history)
  - Week 2: simulated relational *source* (source_departments table)

The ingestion layer uses raw SQL text queries (no ORM models) so
that it remains decoupled from the application's domain models.
"""
import logging
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, SQLAlchemyError

logger = logging.getLogger(__name__)


def ingest_postgres(
    query: str,
    database_url: str,
) -> list[dict[str, Any]]:
    """Execute a read-only SQL query and return results as a list of dicts.

    Creates a short-lived engine for the query, then disposes it.
    This is intentional: ingestion is a batch operation, not a long-lived
    connection pool.

    Args:
        query:        Raw SQL SELECT statement to execute.
        database_url: SQLAlchemy-compatible PostgreSQL connection URL.
                      Must NOT contain credentials in code — pass from
                      settings/environment variables.

    Returns:
        List of dictionaries where keys are column names.

    Raises:
        ConnectionError:  If the database cannot be reached.
        RuntimeError:     If the query fails for any other reason.
    """
    logger.info("PostgreSQL ingestion starting | query=%s", query[:80])

    engine = create_engine(database_url, pool_pre_ping=True)
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query))
            # mappings() gives us dict-like rows; we convert to plain dicts
            records = [dict(row) for row in result.mappings()]

        logger.info("PostgreSQL ingestion complete | records=%d", len(records))
        return records

    except OperationalError as e:
        # Network-level failure: host unreachable, bad credentials, etc.
        logger.error("PostgreSQL connection failed: %s", e)
        raise ConnectionError(f"Cannot connect to PostgreSQL source: {e}") from e

    except SQLAlchemyError as e:
        # Query-level failure: bad SQL, missing table, permission denied, etc.
        logger.error("PostgreSQL query failed: %s", e)
        raise RuntimeError(f"PostgreSQL query failed: {e}") from e

    finally:
        engine.dispose()
