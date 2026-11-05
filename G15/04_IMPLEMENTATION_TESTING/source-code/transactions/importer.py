import csv
import io
from datetime import date
from decimal import Decimal, InvalidOperation

from django.db import transaction as db_transaction

from categories.models import Category
from .models import Transaction


REQUIRED_COLUMNS = ["date", "amount", "type", "category", "note"]
MAX_UPLOAD_BYTES = 2 * 1024 * 1024
MAX_CATEGORY_LENGTH = 100
MAX_NOTE_LENGTH = 250


def import_transactions(file, user):
    """
    Import valid transactions from a CSV file.

    Validates file size, encoding, CSV structure and field values.
    Invalid rows are reported without preventing valid rows from importing.
    """

    imported = 0
    errors = []
    seen_in_file = set()

    try:
        if hasattr(file, "size") and file.size > MAX_UPLOAD_BYTES:
            return {
                "imported": 0,
                "errors": [{
                    "row": 1,
                    "reason": "File must be 2 MB or smaller.",
                }],
            }

        if hasattr(file, "read"):
            raw = file.read()
        else:
            raw = file

        if isinstance(raw, bytes):
            if len(raw) > MAX_UPLOAD_BYTES:
                return {
                    "imported": 0,
                    "errors": [{
                        "row": 1,
                        "reason": "File must be 2 MB or smaller.",
                    }],
                }

            raw = raw.decode("utf-8-sig")

        elif isinstance(raw, str):
            raw = raw.lstrip("\ufeff")

            if len(raw.encode("utf-8")) > MAX_UPLOAD_BYTES:
                return {
                    "imported": 0,
                    "errors": [{
                        "row": 1,
                        "reason": "File must be 2 MB or smaller.",
                    }],
                }
        else:
            return {
                "imported": 0,
                "errors": [{
                    "row": 1,
                    "reason": "Invalid CSV file content.",
                }],
            }

        reader = csv.DictReader(
            io.StringIO(raw, newline=""),
            strict=True,
        )

        if not reader.fieldnames:
            return {
                "imported": 0,
                "errors": [{
                    "row": 1,
                    "reason": "CSV is empty or has no header.",
                }],
            }

        reader.fieldnames = [
            name.strip() if name else ""
            for name in reader.fieldnames
        ]

        if reader.fieldnames != REQUIRED_COLUMNS:
            return {
                "imported": 0,
                "errors": [{
                    "row": 1,
                    "reason": (
                        "Header must be exactly: "
                        "date,amount,type,category,note"
                    ),
                }],
            }

        for row_number, row in enumerate(reader, start=2):
            try:
                # Reject rows with extra or missing columns.
                if None in row or any(value is None for value in row.values()):
                    raise ValueError(
                        "CSV row has missing or extra columns."
                    )

                raw_date = (row.get("date") or "").strip()
                raw_amount = (row.get("amount") or "").strip()
                raw_type = (row.get("type") or "").strip().title()
                category_name = (row.get("category") or "").strip()
                note = (row.get("note") or "").strip()

                # Reject unexpected control characters in text fields.
                for field_value in (category_name, note):
                    if any(
                        ord(character) < 32 and character not in "\t"
                        for character in field_value
                    ):
                        raise ValueError(
                            "Text fields contain invalid control characters."
                        )

                if not category_name:
                    raise ValueError("Category is required.")

                if len(category_name) > MAX_CATEGORY_LENGTH:
                    raise ValueError(
                        "Category name must not exceed 100 characters."
                    )

                if len(note) > MAX_NOTE_LENGTH:
                    raise ValueError(
                        "Note must not exceed 250 characters."
                    )

                parsed_date = date.fromisoformat(raw_date)

                amount = Decimal(raw_amount)

                if not amount.is_finite() or amount <= 0:
                    raise ValueError(
                        "Amount must be greater than zero."
                    )

                if amount.as_tuple().exponent < -2:
                    raise ValueError(
                        "Amount may have at most two decimal places."
                    )

                if raw_type not in (
                    Transaction.TransactionType.EXPENSE,
                    Transaction.TransactionType.INCOME,
                ):
                    raise ValueError(
                        "Type must be Expense or Income."
                    )

                category = Category.objects.filter(
                    name__iexact=category_name,
                    type=raw_type,
                    is_active=True,
                ).first()

                if category is None:
                    raise ValueError(
                        "No matching active category was found."
                    )

                signature = (
                    parsed_date.isoformat(),
                    amount.quantize(Decimal("0.01")),
                    note,
                )

                if signature in seen_in_file:
                    errors.append({
                        "row": row_number,
                        "reason": (
                            "Duplicate transaction row in this CSV file."
                        ),
                    })
                    continue

                duplicate_exists = Transaction.objects.filter(
                    user=user,
                    date=parsed_date,
                    amount=amount,
                    note=note,
                ).exists()

                if duplicate_exists:
                    errors.append({
                        "row": row_number,
                        "reason": (
                            "Duplicate transaction already exists."
                        ),
                    })
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

                seen_in_file.add(signature)
                imported += 1

            except (
                ValueError,
                InvalidOperation,
                TypeError,
                csv.Error,
            ) as exc:
                errors.append({
                    "row": row_number,
                    "reason": str(exc),
                })

    except (UnicodeDecodeError, csv.Error) as exc:
        return {
            "imported": imported,
            "errors": [{
                "row": 1,
                "reason": "Invalid CSV encoding or structure.",
            }],
        }

    return {
        "imported": imported,
        "errors": errors,
    }