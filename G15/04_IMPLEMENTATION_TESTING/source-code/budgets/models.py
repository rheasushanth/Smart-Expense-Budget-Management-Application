from django.conf import settings
from django.db import models


class Budget(models.Model):
    class Period(models.TextChoices):
        WEEKLY = "Weekly", "Weekly"
        MONTHLY = "Monthly", "Monthly"

    budget_id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="budgets",
    )
    category = models.ForeignKey(
        "categories.Category",
        on_delete=models.PROTECT,
        related_name="budgets",
    )
    period = models.CharField(max_length=10, choices=Period.choices)
    limit_amount = models.DecimalField(max_digits=12, decimal_places=2)
    threshold_pct = models.PositiveSmallIntegerField(default=80)

    def __str__(self):
        return f"{self.category.name} - {self.period}"
class Alert(models.Model):
    alert_id = models.BigAutoField(primary_key=True)
    budget = models.ForeignKey(
        Budget,
        on_delete=models.CASCADE,
        related_name="alerts",
    )
    triggered_on = models.DateField(auto_now_add=True)
    message = models.CharField(max_length=250)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Alert for budget {self.budget_id}"
