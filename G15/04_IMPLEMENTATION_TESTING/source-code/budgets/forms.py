from django import forms

from categories.models import Category

from .models import Budget


class BudgetForm(forms.ModelForm):
    """Create and edit form for a budget (FR-012).

    Only active Expense categories are offered, so the category rule in
    SRS Appendix C is enforced in the form as well as in Budget.clean().
    """

    class Meta:
        model = Budget
        fields = ["category", "period", "start_date", "limit_amount", "threshold_pct"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
        }
        labels = {
            "limit_amount": "Limit amount",
            "threshold_pct": "Alert threshold (%)",
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields["category"].queryset = Category.objects.filter(
            type=Category.CategoryType.EXPENSE,
            is_active=True,
        ).order_by("name")

    def _post_clean(self):
        # Attach the owner before Django runs Budget.clean(), so the
        # overlap check (FR-014) can see which user the budget belongs to.
        if self.user is not None:
            self.instance.user = self.user
        super()._post_clean()
