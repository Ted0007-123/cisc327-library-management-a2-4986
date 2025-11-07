# conftest.py (REPO ROOT)
import os
import sys
import sqlite3
import pytest
import importlib

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


import database 

DB_URI = "file:lmstest?mode=memory&cache=shared"

def _open_conn():
    conn = sqlite3.connect(DB_URI, uri=True, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def _create_schema(conn: sqlite3.Connection):
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

@pytest.fixture(autouse=True, scope="session")
def _shared_memdb_session():
    keeper = _open_conn()
    _create_schema(keeper)
    original = getattr(database, "get_db_connection", None)
    database.get_db_connection = _open_conn  # type: ignore[attr-defined]
    try:
        yield
    finally:
        if original:
            database.get_db_connection = original 
        keeper.close()

@pytest.fixture
def temp_db():

    yield

def _load_flask_app():
    app_mod = importlib.import_module("app")
    if hasattr(app_mod, "create_app"):
        return app_mod.create_app()
    return getattr(app_mod, "app", None)

@pytest.fixture(scope="session")
def client():
    app = _load_flask_app()
    if app is None:
        pytest.skip("Flask app not available (app.create_app/app)")
    with app.test_client() as c:
        yield c
