from django import forms


class ReportPeriodForm(forms.Form):
    """Date range for the spending report (FR-017)."""

    start_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        label="From",
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        label="To",
    )

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_date")
        end = cleaned.get("end_date")

        if start and end and start > end:
            raise forms.ValidationError(
                "The start date must not be after the end date."
            )

        return cleaned
