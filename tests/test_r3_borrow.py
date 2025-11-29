import importlib
import pytest

lib = importlib.import_module("library_service")
add_book = getattr(lib, "add_book_to_catalog")
borrow = getattr(lib, "borrow_book_by_patron")  # actual project name

@pytest.mark.usefixtures("temp_db")
def test_r3_borrow_until_out_of_stock():
    """
    R3: Borrow should succeed while copies are available, then fail when none left.
    We add a controlled test book to avoid depending on seed state.
    """
    ok, msg = add_book("Test Borrow", "Author", "1234567890123", 1)
    assert ok

    # First borrow (available = 1 -> 0)
    ok1, msg1 = borrow("123456", 1)  # book_id=1 for the first inserted book in an empty DB
    assert ok1 is True, f"first borrow should succeed: {(ok1, msg1)}"

    # Second borrow should fail (no copies left)
    ok2, msg2 = borrow("123456", 1)
    assert ok2 is False, f"second borrow should fail when out of stock: {(ok2, msg2)}"
