from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError

class Category(models.Model):
    class CategoryType(models.TextChoices):
        EXPENSE = "Expense", "Expense"
        INCOME = "Income", "Income"

    category_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=CategoryType.choices)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_categories",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["name", "type"],
                name="unique_category_name_type",
            )
        ]
    def validate_active(self):
        """Reject assigning a disabled category to a new object (FR-021)."""
        if not self.is_active:
            raise ValidationError(
                "This category has been disabled and cannot be assigned."
            )
    def __str__(self):
        return f"{self.name} ({self.type})"
