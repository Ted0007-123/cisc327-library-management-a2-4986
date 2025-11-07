import importlib
import pytest

lib = importlib.import_module("library_service")
get_status = getattr(lib, "get_patron_status_report")  # actual project name

@pytest.mark.usefixtures("temp_db")
def test_r7_status_report_shape_and_keys():
    """
    R7: Patron status report should include the required keys.
    NOTE: If not implemented yet, this test will fail (which documents the gap).
    """
    report = get_status("123456")
    assert isinstance(report, dict), f"expected dict, got {type(report)}: {report}"

    # Required by the spec:
    for key in ["borrowed_books", "total_late_fees", "active_loans", "history"]:
        assert key in report, f"missing key in status report: {key}"
