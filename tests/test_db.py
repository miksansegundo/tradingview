"""DB smoke tests."""

from src.db.database import init_db, get_connection, log_event


def test_init_db_creates_tables():
    """Tables orders, positions, trade_log should exist after init."""
    with get_connection() as conn:
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
    names = [r["name"] for r in tables]
    assert "orders" in names
    assert "positions" in names
    assert "trade_log" in names


def test_log_event_inserts_row():
    log_event("INFO", "test message", {"key": "val"})
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM trade_log").fetchall()
    assert len(rows) == 1
    assert rows[0]["level"] == "INFO"
    assert rows[0]["message"] == "test message"
