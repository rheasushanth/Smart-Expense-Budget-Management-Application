from django.conf import settings
from django.db import models


class RecurringRule(models.Model):
    class Frequency(models.TextChoices):
        WEEKLY = "Weekly", "Weekly"
        MONTHLY = "Monthly", "Monthly"

    rule_id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recurring_rules",
    )
    category = models.ForeignKey(
        "categories.Category",
        on_delete=models.PROTECT,
        related_name="recurring_rules",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    frequency = models.CharField(max_length=10, choices=Frequency.choices)
    next_run_date = models.DateField()

    def __str__(self):
        return f"{self.category.name} - {self.frequency}"
