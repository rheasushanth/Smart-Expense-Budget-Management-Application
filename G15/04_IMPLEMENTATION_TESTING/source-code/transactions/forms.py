
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
        self.fields["category"].required = True
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
        self.fields["category"].required = True
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
MAX_UPLOAD_BYTES = 2 * 1024 * 1024


class CSVUploadForm(forms.Form):
    csv_file = forms.FileField()

    def clean_csv_file(self):
        upload = self.cleaned_data["csv_file"]

        if upload.size > MAX_UPLOAD_BYTES:
            raise forms.ValidationError(
                "File must be 2 MB or smaller."
            )

        if not upload.name.lower().endswith(".csv"):
            raise forms.ValidationError(
                "Please upload a CSV file."
            )

        return upload