import calendar
from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
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
    start_date = models.DateField()
    limit_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    threshold_pct = models.PositiveSmallIntegerField(
        default=80,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )

    @property
    def period_end(self):
        """Last day covered by this budget (SRS Appendix B.3).

        A Weekly budget covers start_date through start_date + 6 days. A
        Monthly budget covers start_date through the day before the same
        day-of-month in the following month; when that day does not exist,
        it runs through the following month's last day.
        """
        if self.period == self.Period.WEEKLY:
            return self.start_date + timedelta(days=6)

        year, month = self.start_date.year, self.start_date.month
        if month == 12:
            next_year, next_month = year + 1, 1
        else:
            next_year, next_month = year, month + 1

        last_day_of_next = calendar.monthrange(next_year, next_month)[1]
        if self.start_date.day <= last_day_of_next:
            same_day_next_month = date(
                next_year, next_month, self.start_date.day
            )
            return same_day_next_month - timedelta(days=1)

        return date(next_year, next_month, last_day_of_next)

    def overlaps(self, other):
        """True when two budget periods share at least one day."""
        return (
            self.start_date <= other.period_end
            and other.start_date <= self.period_end
        )

    def clean(self):
        """Business rules from SRS Appendix B.3 and Appendix C.

        FR-012: a budget may only be set on an Expense category.
        FR-014: a user may not hold two overlapping budgets for one category.
        """
        super().clean()

        if self.category_id and self.category.type != "Expense":
            raise ValidationError(
                {"category": "A budget can only be set on an Expense category."}
            )

        if not (
            self.user_id
            and self.category_id
            and self.start_date
            and self.period
        ):
            # Not enough information yet to run the overlap check; the field
            # validators have already reported the missing values.
            return

        clashing = Budget.objects.filter(
            user=self.user,
            category=self.category,
        )
        if self.pk:
            clashing = clashing.exclude(pk=self.pk)

        for other in clashing:
            if self.overlaps(other):
                raise ValidationError(
                    {
                        "start_date": (
                            f"This budget overlaps an existing "
                            f"{other.category.name} budget running "
                            f"{other.start_date} to {other.period_end}."
                        )
                    }
                )

    def save(self, *args, **kwargs):
        """Prevent assigning a disabled category to a new budget (FR-021)."""
        if self._state.adding and self.category_id:
            self.category.validate_active()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.category.name} - {self.period}"


class Alert(models.Model):
    class Kind(models.TextChoices):
        THRESHOLD = "Threshold", "Threshold"
        LIMIT = "Limit", "Limit"

    alert_id = models.BigAutoField(primary_key=True)
    budget = models.ForeignKey(
        Budget,
        on_delete=models.CASCADE,
        related_name="alerts",
    )
    kind = models.CharField(max_length=10, choices=Kind.choices)
    triggered_on = models.DateField(auto_now_add=True)
    message = models.CharField(max_length=250)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Alert for budget {self.budget_id}"
