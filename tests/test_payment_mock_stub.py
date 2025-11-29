# tests/test_a3_payment.py
from unittest.mock import Mock, patch
from services.payment_service import PaymentGateway
from services.library_service import pay_late_fees

def test_pay_late_fees_success_basic():
    patron_id = "123456"
    book_id = 1
    with patch("services.library_service.calc_fee_for_book", return_value={"fee": 3.0}):
        gateway = Mock(spec=PaymentGateway)
        gateway.process_payment.return_value = {"transaction_id": "TXN-OK-1"}

        ok, payload = pay_late_fees(patron_id, book_id, gateway)
        assert ok is True
        assert isinstance(payload, dict) and payload.get("transaction_id") == "TXN-OK-1"
        assert payload.get("amount") == 3.0
        gateway.process_payment.assert_called_once_with(patron_id, 3.0)

def test_pay_late_fees_no_fee_skips_gateway():
    from unittest.mock import Mock, patch
    from services.payment_service import PaymentGateway
    from services.library_service import pay_late_fees

    patron_id = "123456"
    book_id = 1

    with patch("services.library_service.calc_fee_for_book", return_value={"fee": 0.0}):
        gateway = Mock(spec=PaymentGateway)

        ok, msg = pay_late_fees(patron_id, book_id, gateway)

        assert ok is False
        assert isinstance(msg, str) and "No late fee" in msg

        gateway.process_payment.assert_not_called()

def test_pay_late_fees_gateway_exception():
    from unittest.mock import Mock, patch
    from services.payment_service import PaymentGateway
    from services.library_service import pay_late_fees

    patron_id = "123456"
    book_id = 1

    with patch("services.library_service.calc_fee_for_book", return_value={"fee": 3.0}):
        gateway = Mock(spec=PaymentGateway)
        gateway.process_payment.side_effect = Exception("declined")

        ok, msg = pay_late_fees(patron_id, book_id, gateway)

        assert ok is False
        assert isinstance(msg, str) and "Payment failed" in msg
        gateway.process_payment.assert_called_once_with(patron_id, 3.0)

def test_pay_late_fees_missing_transaction_id():
    from unittest.mock import Mock, patch
    from services.payment_service import PaymentGateway
    from services.library_service import pay_late_fees

    patron_id = "123456"
    book_id = 1

    with patch("services.library_service.calc_fee_for_book", return_value={"fee": 2.5}):
        gateway = Mock(spec=PaymentGateway)

        gateway.process_payment.return_value = {"status": "ok"}

        ok, msg = pay_late_fees(patron_id, book_id, gateway)

        assert ok is False
        assert isinstance(msg, str) and "transaction id" in msg.lower()
        gateway.process_payment.assert_called_once_with(patron_id, 2.5)

def test_refund_late_fee_success_basic():

    from unittest.mock import Mock
    from services.payment_service import PaymentGateway
    from services.library_service import refund_late_fee_payment

    txid = "TXN-OK-1"
    amount = 3.0

    gateway = Mock(spec=PaymentGateway)
    gateway.refund_payment.return_value = {"refund_id": "REF-OK-1"}

    ok, payload = refund_late_fee_payment(txid, amount, gateway)

    assert ok is True
    assert isinstance(payload, dict)
    assert payload.get("refund_id") == "REF-OK-1"
    assert payload.get("amount") == 3.0
    gateway.refund_payment.assert_called_once_with(txid, amount)

def test_refund_late_fee_reject_non_positive_amount():
    from unittest.mock import Mock
    from services.payment_service import PaymentGateway
    from services.library_service import refund_late_fee_payment

    txid = "TXN-ANY"

    for bad_amount in [0, -1, -3.5]:
        gateway = Mock(spec=PaymentGateway)
        ok, msg = refund_late_fee_payment(txid, bad_amount, gateway)

        assert ok is False
        assert isinstance(msg, str) and "positive" in msg.lower()
        gateway.refund_payment.assert_not_called()

def test_refund_late_fee_reject_exceeds_cap():
    from unittest.mock import Mock
    from services.payment_service import PaymentGateway
    from services.library_service import refund_late_fee_payment

    txid = "TXN-ANY"
    gateway = Mock(spec=PaymentGateway)

    ok, msg = refund_late_fee_payment(txid, 15.01, gateway)

    assert ok is False
    assert isinstance(msg, str) and "exceeds cap" in msg.lower()
    gateway.refund_payment.assert_not_called()


def test_pay_late_fees_invalid_patron_id_formats():
    from unittest.mock import Mock, patch
    from services.payment_service import PaymentGateway
    from services.library_service import pay_late_fees

    bad_ids = ["", "abc", "12345", "1234567"]
    for pid in bad_ids:
        with patch("services.library_service.calc_fee_for_book", return_value={"fee": 3.0}):
            gw = Mock(spec=PaymentGateway)
            ok, msg = pay_late_fees(pid, 1, gw)
            assert ok is False and isinstance(msg, str)
            gw.process_payment.assert_not_called()


def test_pay_late_fees_invalid_book_id():
    from unittest.mock import Mock, patch
    from services.payment_service import PaymentGateway
    from services.library_service import pay_late_fees

    for bad_bid in [0, -1, -10]:
        with patch("services.library_service.calc_fee_for_book", return_value={"fee": 3.0}):
            gw = Mock(spec=PaymentGateway)
            ok, msg = pay_late_fees("123456", bad_bid, gw)
            assert ok is False
            gw.process_payment.assert_not_called()


def test_pay_late_fees_calc_exception():
    from unittest.mock import Mock, patch
    from services.payment_service import PaymentGateway
    from services.library_service import pay_late_fees

    with patch("services.library_service.calc_fee_for_book", side_effect=Exception("calc boom")):
        gw = Mock(spec=PaymentGateway)
        ok, msg = pay_late_fees("123456", 1, gw)
        assert ok is False and "failed to compute" in msg.lower()
        gw.process_payment.assert_not_called()


def test_pay_late_fees_fee_capped_to_15():
    from unittest.mock import Mock, patch
    from services.payment_service import PaymentGateway
    from services.library_service import pay_late_fees

    with patch("services.library_service.calc_fee_for_book", return_value={"fee": 99.99}):
        gw = Mock(spec=PaymentGateway)
        gw.process_payment.return_value = {"transaction_id": "TXN-CAP"}
        ok, payload = pay_late_fees("123456", 1, gw)
        assert ok is True
        assert payload.get("amount") == 15.0
        gw.process_payment.assert_called_once_with("123456", 15.0)


def test_pay_late_fees_accepts_float_return():
    from unittest.mock import Mock, patch
    from services.payment_service import PaymentGateway
    from services.library_service import pay_late_fees

    with patch("services.library_service.calc_fee_for_book", return_value=2.0):
        gw = Mock(spec=PaymentGateway)
        gw.process_payment.return_value = {"transaction_id": "TXN-FLOAT"}
        ok, payload = pay_late_fees("123456", 1, gw)
        assert ok is True and payload.get("amount") == 2.0
        gw.process_payment.assert_called_once_with("123456", 2.0)


def test_pay_late_fees_gateway_missing_method():
    from unittest.mock import patch
    from services.library_service import pay_late_fees

    class Dummy: 
        pass

    with patch("services.library_service.calc_fee_for_book", return_value={"fee": 2.0}):
        ok, msg = pay_late_fees("123456", 1, Dummy())

    assert ok is False and "gateway" in msg.lower()



def test_refund_late_fee_invalid_txid_and_amount_type():
    from unittest.mock import Mock
    from services.payment_service import PaymentGateway
    from services.library_service import refund_late_fee_payment

    gw = Mock(spec=PaymentGateway)
    ok1, msg1 = refund_late_fee_payment("", 3.0, gw)
    ok2, msg2 = refund_late_fee_payment(None, 3.0, gw)
    ok3, msg3 = refund_late_fee_payment("TXN", "abc", gw)

    assert ok1 is False and "transaction" in msg1.lower()
    assert ok2 is False and "transaction" in msg2.lower()
    assert ok3 is False and "invalid amount" in msg3.lower()
    gw.refund_payment.assert_not_called()


def test_refund_late_fee_gateway_exception():
    from unittest.mock import Mock
    from services.payment_service import PaymentGateway
    from services.library_service import refund_late_fee_payment

    gw = Mock(spec=PaymentGateway)
    gw.refund_payment.side_effect = Exception("network down")

    ok, msg = refund_late_fee_payment("TXN-1", 3.0, gw)
    assert ok is False and "refund failed" in msg.lower()
    gw.refund_payment.assert_called_once_with("TXN-1", 3.0)


def test_refund_late_fee_missing_refund_id():
    from unittest.mock import Mock
    from services.payment_service import PaymentGateway
    from services.library_service import refund_late_fee_payment

    gw = Mock(spec=PaymentGateway)
    gw.refund_payment.return_value = {"status": "ok"} 

    ok, msg = refund_late_fee_payment("TXN-1", 3.0, gw)
    assert ok is False and "refund id" in msg.lower()
    gw.refund_payment.assert_called_once_with("TXN-1", 3.0)
