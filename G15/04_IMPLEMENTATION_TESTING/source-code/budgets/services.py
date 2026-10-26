"""Budget business rules (SAD v1.1, Section 3.4 — Budget Service).

Kept out of the views so the calculations can be unit tested without HTTP
(NFR-005, NFR-006).
"""

from decimal import Decimal

from django.db.models import Sum

from transactions.models import Transaction


def spend_for(budget):
    """Cumulative Expense spend recorded against a budget (FR-013).

    Counts only Expense transactions belonging to the budget's owner and
    category whose date falls inside the budget period (SRS Appendix B.3).
    Income is never counted, per the business rule in SRS Appendix C.
    """
    total = Transaction.objects.filter(
        user=budget.user,
        category=budget.category,
        type=Transaction.TransactionType.EXPENSE,
        date__gte=budget.start_date,
        date__lte=budget.period_end,
    ).aggregate(total=Sum("amount"))["total"]

    # SUM drops the scale on SQLite, so a total of 1000.00 comes back as
    # Decimal("1000"). Quantize so money always displays to two places.
    return (total or Decimal("0")).quantize(Decimal("0.01"))


def remaining_for(budget, spend=None):
    """Amount left before the budget limit is reached (FR-017 budget report).

    May be negative once spend has passed the limit.
    """
    if spend is None:
        spend = spend_for(budget)
    return budget.limit_amount - spend


def percentage_used(budget, spend=None):
    """Spend as a percentage of the limit, rounded to one decimal place.

    Used for the progress display and by the alert evaluator (FR-015,
    FR-016) to decide whether the threshold or the limit has been crossed.
    """
    if spend is None:
        spend = spend_for(budget)
    if budget.limit_amount <= 0:
        return Decimal("0.0")
    return (spend / budget.limit_amount * 100).quantize(Decimal("0.1"))


def threshold_amount(budget):
    """Exact spend at which the threshold alert becomes due (FR-015).

    Alerts compare money against this value rather than against the rounded
    percentage from percentage_used: 3999 of a 5000 budget displays as 80.0%
    but is 79.98%, and must not raise an alert (TC-BUD-04).
    """
    return (budget.limit_amount * budget.threshold_pct / 100).quantize(
        Decimal("0.01")
    )


def budget_status(budget):
    """Everything the budget list and report need, in one query pass."""
    spend = spend_for(budget)
    return {
        "budget": budget,
        "spent": spend,
        "remaining": remaining_for(budget, spend),
        "percentage": percentage_used(budget, spend),
        "over_limit": spend > budget.limit_amount,
        "at_threshold": spend >= threshold_amount(budget),
    }
