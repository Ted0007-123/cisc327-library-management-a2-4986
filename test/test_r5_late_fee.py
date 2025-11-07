import importlib
from datetime import datetime, timedelta
import pytest

db = importlib.import_module("database")
lib = importlib.import_module("library_service")
add_book = getattr(lib, "add_book_to_catalog")
calc_fee_for_book = getattr(lib, "calculate_late_fee_for_book")  # used by API

@pytest.mark.usefixtures("temp_db")
@pytest.mark.parametrize("late_days, expected_fee", [
    (0, 0.0),
    (3, 0.5*3),            # first 7 days: $0.50/day
    (7, 0.5*7),            # = $3.50
    (10, 0.5*7 + 1.0*3),   # = $6.50
    (30, 15.0),            # cap at $15
])
def test_r5_fee_formula_via_business_logic(late_days, expected_fee):
    """
    R5: Late fee rules:
      - Overdue after 14 days
      - First 7 overdue days: $0.50/day
      - Afterwards: $1.00/day
      - Cap per book: $15.00
    We simulate a borrow that is overdue by `late_days`.
    """
    # Add a book
    ok, _ = add_book("Late Fee Book", "Auth", "1111111111111", 1)
    assert ok

    # Insert a borrow record with a due_date in the past by `late_days`
    today = datetime.now()
    borrow_date = today - timedelta(days=30)  # long enough
    due_date = today - timedelta(days=late_days)  # overdue by `late_days`
    db.insert_borrow_record("777777", 1, borrow_date, due_date)

    # Calculate fee
    res = calc_fee_for_book("777777", 1)
    # Allow both dict or tuple forms; project returns a number or dict with "fee"
    fee = res.get("fee") if isinstance(res, dict) else float(res)
    assert abs(fee - expected_fee) < 1e-6, f"expected {expected_fee}, got {fee}"
