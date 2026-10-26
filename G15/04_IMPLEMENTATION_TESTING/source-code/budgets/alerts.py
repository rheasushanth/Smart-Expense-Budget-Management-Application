"""Alert Service (SAD v1.1, Section 3.4).

Compares spend against the threshold and the limit for the budgets covering
a saved transaction, and raises an alert once per crossing (FR-015, FR-016).
"""

from .models import Alert, Budget
from .services import percentage_used, spend_for, threshold_amount


def budgets_covering(user, category, on_date):
    """Budgets of this user and category whose period contains on_date."""
    candidates = Budget.objects.filter(user=user, category=category)
    return [b for b in candidates if b.start_date <= on_date <= b.period_end]


def _raise_once(budget, kind, message):
    """Create an alert unless one of this kind already exists for the budget.

    This is what stops a fresh alert being raised on every later transaction
    while spend stays above the mark (TC-BUD-04: no second threshold alert
    at 4100).
    """
    if Alert.objects.filter(budget=budget, kind=kind).exists():
        return None
    return Alert.objects.create(budget=budget, kind=kind, message=message)


def evaluate_budget(budget):
    """Raise any alert now due for one budget. Returns the alerts created."""
    spend = spend_for(budget)
    used = percentage_used(budget, spend)
    created = []

    # FR-016: over budget, strictly above 100% of the limit. Spend equal to
    # the limit is not over budget (TC-BUD-05).
    if spend > budget.limit_amount:
        alert = _raise_once(
            budget,
            Alert.Kind.LIMIT,
            f"{budget.category.name}: spend of {spend} has exceeded the "
            f"budget limit of {budget.limit_amount}.",
        )
        if alert:
            created.append(alert)

    # FR-015: threshold reached, at or above threshold_pct of the limit.
    # Compared against the exact amount rather than the rounded percentage:
    # 3999 of 5000 displays as 80.0% but is 79.98%, and must not alert
    # (TC-BUD-04). 4000 exactly does alert.
    if spend >= threshold_amount(budget):
        alert = _raise_once(
            budget,
            Alert.Kind.THRESHOLD,
            f"{budget.category.name}: spend of {spend} has reached "
            f"{used}% of the {budget.limit_amount} budget.",
        )
        if alert:
            created.append(alert)

    return created


def evaluate(user, category, on_date):
    """Evaluate every budget covering a saved transaction (FR-015, FR-016).

    Called by the post_save hook in budgets/signals.py, so any path that
    creates a transaction — manual entry, CSV import or the recurring rule
    runner — raises alerts without the entry view knowing about them.
    """
    created = []
    for budget in budgets_covering(user, category, on_date):
        created.extend(evaluate_budget(budget))
    return created
