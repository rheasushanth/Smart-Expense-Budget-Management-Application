
import csv
import hashlib
import io
from datetime import date
from decimal import Decimal, InvalidOperation

from django.db import transaction as db_transaction

from categories.models import Category
from .models import Transaction


REQUIRED_COLUMNS = ["date", "amount", "type", "category", "note"]


def import_transactions(file, user):
    """
    Import valid transactions from a CSV file.
    Invalid rows are reported without preventing valid rows from importing.
    """
    imported = 0
    errors = []
    seen_in_file = set()

    try:
        if hasattr(file, "read"):
            raw = file.read()
        else:
            raw = file

        if isinstance(raw, bytes):
            raw = raw.decode("utf-8-sig")
        else:
            raw = raw.lstrip("\ufeff")

        reader = csv.DictReader(io.StringIO(raw))

        if not reader.fieldnames:
            return {"imported": 0, "errors": [{"row": 1, "reason": "CSV is empty or has no header."}]}

        reader.fieldnames = [name.strip() for name in reader.fieldnames]

        if reader.fieldnames != REQUIRED_COLUMNS:
            return {
                "imported": 0,
                "errors": [{
                    "row": 1,
                    "reason": "Header must be exactly: date,amount,type,category,note",
                }],
            }

        for row_number, row in enumerate(reader, start=2):
            try:
                raw_date = (row.get("date") or "").strip()
                raw_amount = (row.get("amount") or "").strip()
                raw_type = (row.get("type") or "").strip().title()
                category_name = (row.get("category") or "").strip()
                note = (row.get("note") or "").strip()

                parsed_date = date.fromisoformat(raw_date)

                amount = Decimal(raw_amount)
                if not amount.is_finite() or amount <= 0:
                    raise ValueError("Amount must be greater than zero.")
                if amount.as_tuple().exponent < -2:
                    raise ValueError("Amount may have at most two decimal places.")

                if raw_type not in (
                    Transaction.TransactionType.EXPENSE,
                    Transaction.TransactionType.INCOME,
                ):
                    raise ValueError("Type must be Expense or Income.")

                if not category_name:
                    raise ValueError("Category is required.")

                if len(note) > 250:
                    raise ValueError("Note must not exceed 250 characters.")

                category = Category.objects.filter(
                    name__iexact=category_name,
                    type=raw_type,
                    is_active=True,
                ).first()

                if category is None:
                    raise ValueError(
                        f"No active {raw_type} category named '{category_name}'."
                    )

                # Use a stable signature to skip duplicates within this file
                # and transactions already imported for this user.
                signature = (
                    parsed_date.isoformat(),
                    amount.quantize(Decimal("0.01")),
                    raw_type,
                    category.category_id,
                    note,
                )

                if signature in seen_in_file:
                    errors.append({
                        "row": row_number,
                        "reason": "Duplicate transaction row in this CSV file.",
                    })
                    continue
                seen_in_file.add(signature)

                duplicate_exists = Transaction.objects.filter(
                    user=user,
                    date=parsed_date,
                    amount=amount,
                    type=raw_type,
                    category=category,
                    note=note,
                ).exists()

                if duplicate_exists:
                    continue

                with db_transaction.atomic():
                    Transaction.objects.create(
                        user=user,
                        category=category,
                        date=parsed_date,
                        amount=amount,
                        type=raw_type,
                        note=note,
                        source=Transaction.Source.CSV,
                    )

                imported += 1

            except (ValueError, InvalidOperation, TypeError) as exc:
                errors.append({"row": row_number, "reason": str(exc)})
            except Exception as exc:
                # Keep row-level errors visible rather than silently losing them.
                errors.append({"row": row_number, "reason": str(exc)})

    except (UnicodeDecodeError, csv.Error) as exc:
        return {"imported": imported, "errors": [{"row": 1, "reason": str(exc)}]}

    return {"imported": imported, "errors": errors}
