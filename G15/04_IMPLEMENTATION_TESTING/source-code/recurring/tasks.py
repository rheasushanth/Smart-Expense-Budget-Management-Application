
from calendar import monthrange
from datetime import date, timedelta

from django.db import transaction
from django.utils import timezone

from transactions.models import Transaction

from .models import RecurringRule
import logging
logger = logging.getLogger(__name__)

def get_next_run_date(current_date, frequency):
    """Calculate the next scheduled date for a recurring rule."""

    if frequency == RecurringRule.Frequency.WEEKLY:
        return current_date + timedelta(days=7)

    if frequency == RecurringRule.Frequency.MONTHLY:
        next_month = current_date.month + 1
        next_year = current_date.year

        if next_month > 12:
            next_month = 1
            next_year += 1

        last_day = monthrange(next_year, next_month)[1]
        next_day = min(current_date.day, last_day)

        return date(next_year, next_month, next_day)

    raise ValueError(f"Unsupported frequency: {frequency}")


def generate_due_transactions(run_date=None):
    """
    Generate transactions for active recurring rules whose
    next_run_date is on or before run_date.

    run_date can be supplied explicitly for reliable testing.
    """

    if run_date is None:
        run_date = timezone.localdate()

    results = {
        "created": 0,
        "skipped": 0,
        "errors": 0,
    }

    due_rule_ids = list(
        RecurringRule.objects.filter(
            is_active=True,
            next_run_date__lte=run_date,
        ).values_list("rule_id", flat=True)
    )

    for rule_id in due_rule_ids:
        try:
            with transaction.atomic():
                rule = (
                    RecurringRule.objects.select_for_update()
                    .select_related("category")
                    .get(rule_id=rule_id)
                )

                # Recheck after acquiring the rule.
                if not rule.is_active or rule.next_run_date > run_date:
                    continue

                # Skip rules whose categories have been disabled.
                if not rule.category.is_active:
                    if not rule.category_disabled:
                        rule.category_disabled = True
                        rule.save(update_fields=["category_disabled"])

                    results["skipped"] += 1
                    continue

                # Generate exactly one transaction for this occurrence.
                Transaction.objects.create(
                    user=rule.user,
                    category=rule.category,
                    amount=rule.amount,
                    type=rule.category.type,
                    date=rule.next_run_date,
                    source=Transaction.Source.RECURRING,
                    rule=rule,
                )

                # Advance the rule only after successful creation.
                rule.next_run_date = get_next_run_date(
                    rule.next_run_date,
                    rule.frequency,
                )
                rule.category_disabled = False
                rule.save(
                    update_fields=["next_run_date", "category_disabled"]
                )

                results["created"] += 1

        except Exception:
            logger.exception(
                "Failed to generate transaction for recurring rule %s",
                rule_id,
            )
            results["errors"] += 1
    return results