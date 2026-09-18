"""Unit tests for database session utilities."""
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import OperationalError

from app.db.session import check_db_connection, get_db


class TestCheckDbConnection:
    def test_returns_true_when_db_reachable(self):
        # Verify real DB is up (integration-style, uses the test DB)
        result = check_db_connection()
        assert result is True

    def test_returns_false_when_db_unreachable(self):
        with patch("app.db.session.engine") as mock_engine:
            mock_engine.connect.side_effect = OperationalError(
                "connection refused", None, None
            )
            result = check_db_connection()
        assert result is False


class TestGetDb:
    def test_get_db_yields_session_and_closes(self):
        """get_db must close the session in the finally block."""
        mock_session = MagicMock()
        with patch("app.db.session.SessionLocal", return_value=mock_session):
            gen = get_db()
            session = next(gen)
            assert session is mock_session
            with pytest.raises(StopIteration):
                next(gen)
            mock_session.close.assert_called_once()

    def test_get_db_closes_session_even_on_exception(self):
        """Session must be closed even if an exception is raised during the request."""
        mock_session = MagicMock()
        with patch("app.db.session.SessionLocal", return_value=mock_session):
            gen = get_db()
            next(gen)
            try:
                gen.throw(RuntimeError("simulated error"))
            except RuntimeError:
                pass
            mock_session.close.assert_called_once()
