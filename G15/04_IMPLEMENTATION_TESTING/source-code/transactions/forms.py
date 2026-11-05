from django import forms

from categories.models import Category
from .models import Transaction


MAX_UPLOAD_BYTES = 2 * 1024 * 1024
MAX_NOTE_LENGTH = 250


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

    def clean_note(self):
        note = self.cleaned_data.get("note", "")

        if len(note) > MAX_NOTE_LENGTH:
            raise forms.ValidationError(
                "Note must not exceed 250 characters."
            )

        return note


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

    def clean_note(self):
        note = self.cleaned_data.get("note", "")

        if len(note) > MAX_NOTE_LENGTH:
            raise forms.ValidationError(
                "Note must not exceed 250 characters."
            )

        return note


class CSVUploadForm(forms.Form):
    csv_file = forms.FileField()

    def clean_csv_file(self):
        upload = self.cleaned_data["csv_file"]

        # Validate file size.
        if upload.size > MAX_UPLOAD_BYTES:
            raise forms.ValidationError(
                "File must be 2 MB or smaller."
            )

        # Validate file extension.
        if not upload.name.lower().endswith(".csv"):
            raise forms.ValidationError(
                "Please upload a CSV file."
            )

        # Validate filename.
        if (
            not upload.name
            or upload.name in (".", "..")
            or "/" in upload.name
            or "\\" in upload.name
        ):
            raise forms.ValidationError(
                "Invalid filename."
            )

        # Validate UTF-8 encoding without consuming the upload.
        try:
            upload.seek(0)
            content = upload.read()
            content.decode("utf-8-sig")
            upload.seek(0)
        except (UnicodeDecodeError, OSError):
            raise forms.ValidationError(
                "CSV file must use UTF-8 encoding."
            )

        return upload