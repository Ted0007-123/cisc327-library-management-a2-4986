import importlib
import pytest

lib = importlib.import_module("library_service")
add_book = getattr(lib, "add_book_to_catalog")
borrow = getattr(lib, "borrow_book_by_patron")
ret = getattr(lib, "return_book_by_patron")

@pytest.mark.usefixtures("temp_db")
def test_r4_return_happy_path():
    """
    R4: Borrow then return should succeed.
    """
    ok, _ = add_book("Returnable", "Auth", "9999999999999", 1)
    assert ok

    ok_b, _ = borrow("654321", 1)
    assert ok_b, "borrow must succeed before return"

    ok_r, msg_r = ret("654321", 1)
    assert ok_r is True, f"return should succeed: {(ok_r, msg_r)}"
