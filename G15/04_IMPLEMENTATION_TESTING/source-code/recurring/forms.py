from django import forms

from categories.models import Category

from .models import RecurringRule


class RecurringRuleForm(forms.ModelForm):
    """Create and edit form for a recurring rule (FR-019).

    Only active categories are offered. Both Expense and Income categories
    are valid: the generated transaction takes its type from the category
    (SRS Appendix C).
    """

    class Meta:
        model = RecurringRule
        fields = ["category", "amount", "frequency", "next_run_date"]
        widgets = {
            "next_run_date": forms.DateInput(attrs={"type": "date"}),
        }
        labels = {
            "next_run_date": "Next run date",
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields["category"].queryset = Category.objects.filter(
            is_active=True
        ).order_by("type", "name")

    def _post_clean(self):
        # Attach the owner before the model's own validation runs.
        if self.user is not None:
            self.instance.user = self.user
        super()._post_clean()
