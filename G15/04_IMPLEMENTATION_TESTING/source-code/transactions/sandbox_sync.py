
"""
FR-023: Sandbox bank transaction synchronization service.
"""

from django.db import IntegrityError, transaction as db_transaction

from categories.models import Category
from .models import Transaction, SandboxTransactionImport
from .sandbox_adapter import (
    fetch_bank_transactions,
    validate_bank_transaction,
    SandboxAPIError,
)


def sync_sandbox_transactions(user):
    """
    Fetch, validate and import sandbox bank transactions for a user.

    Returns imported count, skipped count and row-level errors.
    """

    imported = 0
    skipped = 0
    errors = []

    try:
        bank_transactions = fetch_bank_transactions()
    except SandboxAPIError as exc:
        return {
            "imported": 0,
            "skipped": 0,
            "errors": [{"reason": str(exc)}],
        }

    if not isinstance(bank_transactions, list):
        return {
            "imported": 0,
            "skipped": 0,
            "errors": [{"reason": "Invalid sandbox API response."}],
        }

    for index, raw_transaction in enumerate(bank_transactions, start=1):
        try:
            data = validate_bank_transaction(raw_transaction)

            if SandboxTransactionImport.objects.filter(
                user=user,
                bank_transaction_id=data["transaction_id"],
            ).exists():
                skipped += 1
                continue

            category = Category.objects.filter(
                name__iexact=data["category"],
                type=data["type"],
                is_active=True,
            ).first()

            if category is None:
                raise ValueError(
                    f"No active {data['type']} category "
                    f"named '{data['category']}'."
                )

            with db_transaction.atomic():
                if SandboxTransactionImport.objects.filter(
                    user=user,
                    bank_transaction_id=data["transaction_id"],
                ).exists():
                    skipped += 1
                    continue

                saved_transaction = Transaction.objects.create(
                    user=user,
                    category=category,
                    date=data["date"],
                    amount=data["amount"],
                    type=data["type"],
                    note=data["note"],
                    source=Transaction.Source.SANDBOX,
                )

                SandboxTransactionImport.objects.create(
                    user=user,
                    bank_transaction_id=data["transaction_id"],
                    transaction=saved_transaction,
                )

            imported += 1

        except IntegrityError:
            skipped += 1

        except Exception as exc:
            errors.append({
                "row": index,
                "reason": str(exc),
            })

    return {
        "imported": imported,
        "skipped": skipped,
        "errors": errors,
    }
