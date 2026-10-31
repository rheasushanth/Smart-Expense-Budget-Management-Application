
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
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
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    frequency = models.CharField(max_length=10, choices=Frequency.choices)
    next_run_date = models.DateField()
    is_active = models.BooleanField(default=True)
    category_disabled = models.BooleanField(default=False)

    def clean(self):
        """A rule may only use an active category (SRS Appendix B.5, FR-021).

        The rule has no type of its own: each transaction it generates takes
        its type from the category, so both Expense and Income categories are
        allowed here.
        """
        super().clean()

        if self.category_id and not self.category.is_active:
            raise ValidationError(
                {
                    "category": (
                        "This category has been disabled and cannot be used."
                    )
                }
            )

    def save(self, *args, **kwargs):
        """Prevent assigning a disabled category to a new recurring rule."""
        if self._state.adding and self.category_id:
            self.category.validate_active()

        super().save(*args, **kwargs)

    def deactivate(self):
        """Stop the rule generating further transactions (FR-019)."""
        self.is_active = False
        self.save(update_fields=["is_active"])

    def __str__(self):
        return f"{self.category.name} - {self.frequency}"
