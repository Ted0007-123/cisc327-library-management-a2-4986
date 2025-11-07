class PaymentGateway:
    def process_payment(self, patron_id: str, amount: float) -> dict:
        return {
            "transaction_id": "TXN123456",
            "status": f"Processed ${amount:.2f} for patron {patron_id}"
        }

    def refund_payment(self, transaction_id: str, amount: float) -> dict:
        return {
            "refund_id": "REF987654",
            "status": f"Refunded ${amount:.2f} for transaction {transaction_id}"
        }
