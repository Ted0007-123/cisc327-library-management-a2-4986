
import os
import sys
import sqlite3
import pytest
import importlib
import uuid

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import database  # noqa: E402


def _create_schema(conn: sqlite3.Connection):
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            isbn TEXT UNIQUE NOT NULL,
            total_copies INTEGER NOT NULL,
            available_copies INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS borrow_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patron_id TEXT NOT NULL,
            book_id INTEGER NOT NULL,
            borrow_date TEXT NOT NULL,
            due_date TEXT NOT NULL,
            return_date TEXT,
            FOREIGN KEY (book_id) REFERENCES books(id)
        );

        CREATE TABLE IF NOT EXISTS patrons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patron_id TEXT UNIQUE,
            name TEXT,
            email TEXT
        );
        """
    )


def _open_conn(db_uri: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_uri, uri=True, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


@pytest.fixture(autouse=True)
def _per_test_memdb(monkeypatch):
    db_uri = f"file:lmstest_{uuid.uuid4().hex}?mode=memory&cache=shared"
    keeper = _open_conn(db_uri)   
    _create_schema(keeper)

    def _get_conn():
        return _open_conn(db_uri)

    monkeypatch.setattr(database, "get_db_connection", _get_conn)

    try:
        yield
    finally:
        keeper.close()


@pytest.fixture
def temp_db():
    yield

def _load_flask_app():
    app_mod = importlib.import_module("app")
    if hasattr(app_mod, "create_app"):
        return app_mod.create_app()
    return getattr(app_mod, "app", None)

@pytest.fixture
def client(temp_db):
    app = _load_flask_app()
    if app is None:
        pytest.skip("Flask app not available (app.create_app/app)")
    with app.test_client() as c:
        yield c
