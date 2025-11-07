"""
Library Service Module - Business Logic Functions
Contains all the core business logic for the Library Management System
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from database import (
    get_book_by_id, get_book_by_isbn, get_patron_borrow_count,
    insert_book, insert_borrow_record, update_book_availability,
    update_borrow_record_return_date, get_all_books,
    search_books_case_insensitive, get_patron_borrowed_books,
    get_patron_history, get_active_borrow_due_date, compute_late_fee_from_due
)
from services.payment_service import PaymentGateway 

def add_book_to_catalog(title: str, author: str, isbn: str, total_copies: int) -> Tuple[bool, str]:
    """
    Add a new book to the catalog.
    Implements R1: Book Catalog Management
    """
    # Input validation
    if not title or not title.strip():
        return False, "Title is required."
    if len(title.strip()) > 200:
        return False, "Title must be less than 200 characters."
    if not author or not author.strip():
        return False, "Author is required."
    if len(author.strip()) > 100:
        return False, "Author must be less than 100 characters."
    if len(isbn) != 13 or not isbn.isdigit():
        return False, "ISBN must be exactly 13 digits."
    if not isinstance(total_copies, int) or total_copies <= 0:
        return False, "Total copies must be a positive integer."
    
    # Check for duplicate ISBN
    existing = get_book_by_isbn(isbn)
    if existing:
        return False, "A book with this ISBN already exists."
    
    # Insert new book
    success = insert_book(title.strip(), author.strip(), isbn, total_copies, total_copies)
    if success:
        return True, f'Book "{title.strip()}" has been successfully added to the catalog.'
    else:
        return False, "Database error occurred while adding the book."

# Alias some names that tests might use
add_book = add_book_to_catalog

def borrow_book_by_patron(patron_id: str, book_id: int) -> Tuple[bool, str]:
    """
    Allow a patron to borrow a book.
    Implements R3 as per requirements  
    """
    # Validate patron ID
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return False, "Invalid patron ID. Must be exactly 6 digits."
    
    # Check if book exists and is available
    book = get_book_by_id(book_id)
    if not book:
        return False, "Book not found."
    if book['available_copies'] <= 0:
        return False, "This book is currently not available."
    
    # Check patron's current borrowed books count
    current_borrowed = get_patron_borrow_count(patron_id)
    if current_borrowed > 5:
        return False, "You have reached the maximum borrowing limit of 5 books."
    
    # Create borrow record
    borrow_date = datetime.now()
    due_date = borrow_date + timedelta(days=14)
    
    # Insert borrow record and update availability
    if not insert_borrow_record(patron_id, book_id, borrow_date, due_date):
        return False, "Database error occurred while creating borrow record."
    if not update_book_availability(book_id, -1):
        return False, "Database error occurred while updating book availability."
    
    return True, f'Successfully borrowed "{book["title"]}". Due date: {due_date.strftime("%Y-%m-%d")}.'

# Alias used by some tests
borrow = borrow_book_by_patron

def return_book_by_patron(patron_id: str, book_id: int) -> Tuple[bool, str]:
    """
    Process book return by a patron.
    Implements R4
    """
    if not update_borrow_record_return_date(patron_id, book_id, datetime.now()):
        return False, "No active loan."
    if not update_book_availability(book_id, +1):
        return False, "Failed to restore inventory."
    return True, "Return successful."

# Alias used by some tests
ret = return_book_by_patron

def calculate_late_fee_for_book(patron_id: str, book_id: int) -> Dict:
    """
    Calculate late fees for a specific book.
    Implements R5
    """
    due = get_active_borrow_due_date(patron_id, book_id)
    if not due:
        return {"fee": 0.0}
    fee = compute_late_fee_from_due(due)
    return {"fee": fee}

# Alias in some tests
calc_fee_for_book = calculate_late_fee_for_book

def search_books_in_catalog(search_term: str, search_type: str) -> List[Dict]:
    """
    Search for books in the catalog (case-insensitive).
    Implements R6
    """
    return search_books_case_insensitive(search_term or "", (search_type or "title"))

# Alias used by some tests
search = search_books_in_catalog

def get_patron_status_report(patron_id: str) -> Dict:
    """
    Get status report for a patron.
    Implements R7
    """
    active = get_patron_borrowed_books(patron_id)
    history = get_patron_history(patron_id)

    # Sum of late fees across active loans
    total_fees = 0.0
    for r in active:
        total_fees += compute_late_fee_from_due(r["due_date"])

    return {
        "borrowed_books": [r["book_id"] for r in active],
        "total_late_fees": round(total_fees, 2),
        "active_loans": len(active),
        "history": history,
    }

# Alias used by some tests
get_status = get_patron_status_report

def pay_late_fees(patron_id: str, book_id: int, payment_gateway: "PaymentGateway"):
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return False, "Invalid patron ID. Must be exactly 6 digits."
    if not isinstance(book_id, int) or book_id <= 0:
        return False, "Invalid book_id."

    try:
        res = calc_fee_for_book(patron_id, book_id)
        fee = res.get("fee") if isinstance(res, dict) else float(res)
    except Exception:
        return False, "Failed to compute late fee."

    if fee is None or fee <= 0.0:
        return False, "No late fee to pay."

    if fee > 15.0:
        fee = 15.0

    if not isinstance(payment_gateway, PaymentGateway):
        if not hasattr(payment_gateway, "process_payment"):
            return False, "Payment gateway not available."

    try:
        resp = payment_gateway.process_payment(patron_id, float(fee))
    except Exception as e:
        return False, f"Payment failed: {e}"

    txid = None
    if isinstance(resp, dict):
        txid = resp.get("transaction_id") or resp.get("txid")

    if not txid:
        return False, "Payment gateway did not return a transaction id."

    return True, {"transaction_id": txid, "amount": round(float(fee), 2)}


def refund_late_fee_payment(transaction_id: str, amount: float, payment_gateway: "PaymentGateway"):
    if not transaction_id or not isinstance(transaction_id, str):
        return False, "Invalid transaction id."
    try:
        amount = float(amount)
    except Exception:
        return False, "Invalid amount."
    if amount <= 0.0:
        return False, "Refund amount must be positive."
    if amount > 15.0:
        return False, "Refund amount exceeds cap ($15.00)."

    if not hasattr(payment_gateway, "refund_payment"):
        return False, "Payment gateway not available."

    try:
        resp = payment_gateway.refund_payment(transaction_id, amount)
    except Exception as e:
        return False, f"Refund failed: {e}"

    refund_id = None
    if isinstance(resp, dict):
        refund_id = resp.get("refund_id") or resp.get("id")

    if not refund_id:
        return False, "Payment gateway did not return a refund id."

    return True, {"refund_id": refund_id, "amount": round(amount, 2)}
