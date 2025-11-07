import importlib
import pytest

lib = importlib.import_module("library_service")
add_book = getattr(lib, "add_book_to_catalog")
search = getattr(lib, "search_books_in_catalog")  # actual project name

@pytest.mark.usefixtures("temp_db")
def test_r6_title_case_insensitive_business_logic():
    """
    R6 (business logic): case-insensitive title search should find matches.
    """
    ok, _ = add_book("Clean Architecture", "Robert C. Martin", "9780134494166", 2)
    assert ok
    r1 = search("clean", "title")
    r2 = search("CLEAN", "title")
    assert isinstance(r1, list) and isinstance(r2, list)
    assert len(r1) >= 1 and len(r2) >= 1, "should return at least one match for sample title"

@pytest.mark.usefixtures("temp_db")
def test_r6_api_json_search(client):
    """
    R6 (API): /api/search should return normalized JSON with 'results' and 'count'.
    """
    # Seed a predictable book
    add_book("Domain-Driven Design", "Eric Evans", "9780321125217", 1)
    resp = client.get("/api/search?q=domain&type=title")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "results" in data and "count" in data
    assert isinstance(data["results"], list) and isinstance(data["count"], int)
    assert data["count"] >= 1
