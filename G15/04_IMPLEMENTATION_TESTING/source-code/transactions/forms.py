
from django import forms

from categories.models import Category
from .models import Transaction


class IncomeForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ["amount", "category", "date", "note"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "note": forms.TextInput(
                attrs={"placeholder": "Optional note"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = Category.objects.filter(
            type=Category.CategoryType.INCOME,
            is_active=True,
        )

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if amount <= 0:
            raise forms.ValidationError(
                "Amount must be greater than zero."
            )
        return amount

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ["amount", "category", "date", "note"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "note": forms.TextInput(
                attrs={"placeholder": "Optional note"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = Category.objects.filter(
            type=Category.CategoryType.EXPENSE,
            is_active=True,
        )

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if amount <= 0:
            raise forms.ValidationError(
                "Amount must be greater than zero."
            )
        return amount
