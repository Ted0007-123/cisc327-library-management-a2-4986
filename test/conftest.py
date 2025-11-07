import os
import importlib
import pytest

# We rely on the real app factory and database helpers provided by the project.
# No aliasing is required; tests call the actual function names used in the codebase.

def _load_app():
    app_mod = importlib.import_module("app")
    # Prefer factory pattern
    if hasattr(app_mod, "create_app"):
        return app_mod.create_app()
    # Fallback: some apps expose a global `app`
    return getattr(app_mod, "app", None)

@pytest.fixture(scope="session")
def flask_app():
    """Create a Flask app once per test session."""
    app = _load_app()
    if app is None:
        pytest.skip("Flask app not available (app.create_app/app)")
    return app

@pytest.fixture()
def client(flask_app):
    """Flask test client."""
    return flask_app.test_client()

@pytest.fixture(autouse=False)
def temp_db(tmp_path, monkeypatch):
    """
    Provide an isolated working directory per test so that
    database.DATABASE = 'library.db' is created in a temp location.
    Also initialize schema and seed sample data.
    """
    # Work in a temporary directory so 'library.db' is placed here.
    monkeypatch.chdir(tmp_path)

    db = importlib.import_module("database")
    # Some projects use init_database(), others init_db()
    init = getattr(db, "init_database", None) or getattr(db, "init_db", None)
    assert init is not None, "No init_database/init_db in database.py"

    init()
    # Optional sample data to make UI/API tests deterministic
    add_seed = getattr(db, "add_sample_data", None)
    if add_seed:
        add_seed()

    yield  # run the test

    # Teardown: nothing special; tmp_path is removed by pytest
