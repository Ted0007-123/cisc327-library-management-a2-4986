# conftest.py (REPO ROOT)
import os
import sys
import sqlite3
import pytest


PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import database


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


@pytest.fixture(autouse=True)
def _auto_inmemory_db(monkeypatch):
    conn = sqlite3.connect(":memory:")
    _create_schema(conn)
    monkeypatch.setattr(database, "get_db_connection", lambda: conn)
    try:
        yield
    finally:
        conn.close()


@pytest.fixture
def temp_db():
    yield
