from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .forms import ReportPeriodForm
from .queries import budget_adherence, category_report, month_bounds


@login_required
def report_view(request):
    """Spending report by category plus budget adherence (FR-017).

    The period defaults to the current month; a date range can be supplied
    through the query string so a report stays shareable as a URL.
    """
    start_date, end_date = month_bounds()

    if request.GET:
        # Keep the bound form even when it fails validation, so the error is
        # shown rather than the bad range being silently ignored.
        form = ReportPeriodForm(request.GET)
        if form.is_valid():
            start_date = form.cleaned_data["start_date"]
            end_date = form.cleaned_data["end_date"]
    else:
        form = ReportPeriodForm(
            initial={"start_date": start_date, "end_date": end_date}
        )

    spending = category_report(request.user, start_date, end_date)

    return render(
        request,
        "reports/report.html",
        {
            "form": form,
            "start_date": start_date,
            "end_date": end_date,
            "spending": spending,
            "adherence": budget_adherence(request.user),
        },
    )
