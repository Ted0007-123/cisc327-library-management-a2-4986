import pytest

@pytest.mark.usefixtures("temp_db")
def test_r2_catalog_route_ok(client):
    """
    R2: "/" should load or redirect to '/catalog' and return 200 eventually.
    """
    r = client.get("/", follow_redirects=True)
    assert r.status_code == 200
    assert b"catalog" in r.data.lower() or b"<table" in r.data.lower()
