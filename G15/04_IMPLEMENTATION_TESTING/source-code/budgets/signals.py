"""Observer hook described in SAD v1.1, Section 3.5.

Alert evaluation is raised after a transaction is saved, so the alert logic
stays decoupled from the entry views. Any path that creates a transaction —
manual entry (FR-005), CSV import (FR-009) or the recurring rule runner
(FR-024) — triggers it without extra wiring.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from transactions.models import Transaction

from .alerts import evaluate


@receiver(post_save, sender=Transaction, dispatch_uid="budgets_evaluate_alerts")
def evaluate_alerts_after_transaction(sender, instance, **kwargs):
    """Evaluate budget alerts for the saved transaction (FR-015, FR-016)."""
    if instance.type != Transaction.TransactionType.EXPENSE:
        # Budgets count Expense transactions only (SRS Appendix C).
        return
    evaluate(instance.user, instance.category, instance.date)
