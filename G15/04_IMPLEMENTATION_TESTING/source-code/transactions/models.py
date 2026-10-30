from django.conf import settings
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError


class Transaction(models.Model):
    class TransactionType(models.TextChoices):
        EXPENSE = "Expense", "Expense"
        INCOME = "Income", "Income"

    class Source(models.TextChoices):
        MANUAL = "Manual", "Manual"
        CSV = "CSV", "CSV"
        RECURRING = "Recurring", "Recurring"
        SANDBOX = "Sandbox", "Sandbox"

    txn_id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    category = models.ForeignKey(
        "categories.Category",
        on_delete=models.PROTECT,
        related_name="transactions",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    type = models.CharField(
        max_length=10,
        choices=TransactionType.choices,
    )
    date = models.DateField(default=timezone.localdate)
    note = models.CharField(max_length=250, blank=True)
    source = models.CharField(
        max_length=10,
        choices=Source.choices,
        default=Source.MANUAL,
    )
    rule = models.ForeignKey(
        "recurring.RecurringRule",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )
    def save(self, *args, **kwargs):
        # FR-021: prevent disabled categories from being assigned
        # to new transactions.
        if self._state.adding and self.category_id:
            self.category.validate_active()

        super().save(*args, **kwargs)
    def __str__(self):
        return f"{self.type}: {self.amount} on {self.date}"
