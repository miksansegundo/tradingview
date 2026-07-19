"""SQLite database setup and helpers."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from src.config import SETTINGS


def _get_db_path() -> str:
    path = Path(SETTINGS.db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return str(path)


def get_connection() -> sqlite3.Connection:
    """Return a new connection. Caller MUST close."""
    conn = sqlite3.connect(_get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    """Create tables if they don't exist."""
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS orders (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol      TEXT NOT NULL,
                side        TEXT NOT NULL CHECK(side IN ('buy','sell')),
                order_type  TEXT NOT NULL DEFAULT 'market',
                qty         INTEGER NOT NULL,
                price       REAL,
                status      TEXT NOT NULL DEFAULT 'pending'
                            CHECK(status IN ('pending','filled','cancelled','rejected')),
                signal_id   TEXT UNIQUE,
                created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                filled_at   TEXT,
                fill_price  REAL,
                notes       TEXT
            );

            CREATE TABLE IF NOT EXISTS positions (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol          TEXT NOT NULL,
                side            TEXT NOT NULL CHECK(side IN ('long','short')),
                qty             INTEGER NOT NULL,
                entry_price     REAL NOT NULL,
                current_price   REAL NOT NULL,
                unrealized_pnl  REAL NOT NULL DEFAULT 0.0,
                opened_at       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                updated_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
            );

            CREATE TABLE IF NOT EXISTS trade_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                level       TEXT NOT NULL DEFAULT 'INFO',
                message     TEXT NOT NULL,
                payload     TEXT
            );
        """)


def log_event(level: str, message: str, payload: dict[str, Any] | None = None) -> None:
    """Insert a row into the trade_log table."""
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO trade_log (level, message, payload) VALUES (?, ?, ?)",
            (level, message, json.dumps(payload) if payload else None),
        )
