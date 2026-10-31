
"""
FR-023: Sandbox Bank Transaction Sync Adapter.

Provides a mock bank integration for development and testing.
No real banking credentials or accounts are used.
"""

from datetime import date
from decimal import Decimal, InvalidOperation


class SandboxAPIError(Exception):
    """Raised when the sandbox bank service is unavailable."""


def fetch_bank_transactions():
    """
    Fetch mock transactions from the sandbox bank service.

    Replace this mock implementation with an HTTP API integration
    when an actual sandbox provider is configured.
    """

    # Simulated sandbox bank response.
    return [
        {
            "transaction_id": "BANK-TXN-001",
            "date": "2026-10-25",
            "amount": "2500.00",
            "type": "Expense",
            "category": "Food",
            "note": "Restaurant payment",
        },
        {
            "transaction_id": "BANK-TXN-002",
            "date": "2026-10-26",
            "amount": "15000.00",
            "type": "Income",
            "category": "Salary",
            "note": "Salary credited",
        },
        {
            "transaction_id": "BANK-TXN-003",
            "date": "2026-10-27",
            "amount": "500.00",
            "type": "Expense",
            "category": "Food",
            "note": "Grocery purchase",
        },
    ]


def validate_bank_transaction(transaction):
    """
    Validate a transaction received from the sandbox.
    """

    required_fields = {
        "transaction_id",
        "date",
        "amount",
        "type",
        "category",
        "note",
    }

    if not isinstance(transaction, dict):
        raise ValueError("Transaction must be a dictionary.")

    if not required_fields.issubset(transaction):
        raise ValueError("Missing required transaction fields.")

    transaction_id = transaction["transaction_id"]

    if not isinstance(transaction_id, str) or not transaction_id.strip():
        raise ValueError("Invalid bank transaction ID.")

    try:
        parsed_date = date.fromisoformat(transaction["date"])
        amount = Decimal(str(transaction["amount"]))
    except (ValueError, TypeError, InvalidOperation):
        raise ValueError("Invalid transaction date or amount.")

    if not amount.is_finite() or amount <= 0:
        raise ValueError("Amount must be greater than zero.")

    if amount.as_tuple().exponent < -2:
        raise ValueError("Amount cannot have more than two decimal places.")

    transaction_type = transaction["type"]

    if transaction_type not in ("Income", "Expense"):
        raise ValueError("Transaction type must be Income or Expense.")

    category = transaction["category"]
    note = transaction["note"]

    if not isinstance(category, str) or not category.strip():
        raise ValueError("Category is required.")

    if not isinstance(note, str) or len(note) > 250:
        raise ValueError("Invalid transaction note.")

    return {
        "transaction_id": transaction_id.strip(),
        "date": parsed_date,
        "amount": amount,
        "type": transaction_type,
        "category": category.strip(),
        "note": note,
    }
