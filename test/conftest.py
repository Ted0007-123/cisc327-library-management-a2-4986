import os
import sys
import importlib
import sqlite3
import pytest

THIS_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(THIS_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import database 


def _load_app():
    app_mod = importlib.import_module("app")
    if hasattr(app_mod, "create_app"):
        return app_mod.create_app()
    return getattr(app_mod, "app", None)


@pytest.fixture(scope="session")
def flask_app():
    app = _load_app()
    if app is None:
        pytest.skip("Flask app not available (app.create_app/app)")
    return app


@pytest.fixture()
def client(flask_app):
    """Flask test client."""
    return flask_app.test_client()


@pytest.fixture(autouse=True)
def in_memory_db(monkeypatch):
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            isbn TEXT UNIQUE NOT NULL,
            copies INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS borrows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patron_id TEXT NOT NULL,
            book_id INTEGER NOT NULL,
            borrow_date TEXT NOT NULL,
            due_date TEXT NOT NULL,
            return_date TEXT
        );

        CREATE TABLE IF NOT EXISTS patrons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patron_id TEXT UNIQUE,
            name TEXT,
            email TEXT
        );
        """
    )

    monkeypatch.setattr(database, "get_db_connection", lambda: conn)

    yield
    conn.close()
