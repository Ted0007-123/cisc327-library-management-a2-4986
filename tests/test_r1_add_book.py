import importlib
import pytest

lib = importlib.import_module("library_service")
add_book = getattr(lib, "add_book_to_catalog")  # project uses this name

@pytest.mark.usefixtures("temp_db")
def test_r1_accepts_valid_input():
    """R1: valid book should be accepted."""
    ok, msg = add_book("Clean Code", "Robert C. Martin", "9780132350884", 3)
    assert ok is True, f"expected success=True, got {(ok, msg)}"

@pytest.mark.usefixtures("temp_db")
def test_r1_rejects_bad_isbn_length():
    """R1: ISBN must be exactly 13 digits."""
    ok, msg = add_book("X", "Y", "12345", 1)
    assert ok is False, "short ISBN should be rejected"

@pytest.mark.usefixtures("temp_db")
def test_r1_rejects_non_positive_total():
    """R1: total copies must be positive integer."""
    ok, msg = add_book("Z", "A", "1234567890123", 0)
    assert ok is False, "non-positive total copies should be rejected"
