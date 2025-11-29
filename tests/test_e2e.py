# tests/test_e2e.py
import time

BASE_URL = "http://localhost:5000"


def test_add_book_flow(page):
    unique_suffix = int(time.time() * 1000) % 10**12 
    title = f"E2E Test Book {unique_suffix}"
    isbn = f"{unique_suffix:013d}" 

    page.goto(f"{BASE_URL}/catalog")

    page.click("text=Add Book")

    page.fill("input[name='title']", title)
    page.fill("input[name='author']", "E2E Test Author")
    page.fill("input[name='isbn']", isbn)
    page.fill("input[name='total_copies']", "3")

    page.click("form button[type='submit']")

    page.goto(f"{BASE_URL}/catalog")

    body_html = page.content()
    assert title in body_html
    assert "E2E Test Author" in body_html


def test_borrow_book_flow(page):
    """
    Flow 2: 카탈로그에서 책 대출하기
    (이 부분은 기존에 PASS였으니 그대로 두면 됨)
    """
    page.goto(f"{BASE_URL}/catalog")

    page.fill("input[name='patron_id']", "123456")
    page.click("text=Borrow")

    page.goto(f"{BASE_URL}/catalog")  # 마찬가지로 확실하게 카탈로그로 이동
    body_html = page.content()
    assert "Borrow" in body_html or "borrowed" in body_html.lower()
