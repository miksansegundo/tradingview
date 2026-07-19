"""Shared fixtures for tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.db.database import init_db, get_connection
from src.main import app


@pytest.fixture(autouse=True)
def _test_db(tmp_path):
    """Override DB path to a temp file and init tables before each test."""
    from src.config import SETTINGS
    original = SETTINGS.db_path
    SETTINGS.db_path = str(tmp_path / "test.db")
    init_db()
    yield
    SETTINGS.db_path = original


@pytest.fixture
def client():
    return TestClient(app)
