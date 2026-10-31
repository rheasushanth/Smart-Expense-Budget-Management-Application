from datetime import date

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render

from .forms import ReportPeriodForm
from .queries import (
    CHART_KINDS,
    GROUPINGS,
    InvalidPeriod,
    UnknownChartKind,
    budget_adherence,
    category_report,
    chart_data,
    month_bounds,
)


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


@login_required
def dashboard_view(request):
    """Analytics dashboard: pie, bar and line charts of spending (FR-018).

    The page renders only the canvases and the period form; the figures are
    fetched from chart_data_view, so the dashboard and the report in
    report_view are drawn from one source (SAD v1.1 Section 4.5).
    """
    start_date, end_date = month_bounds()

    if request.GET:
        form = ReportPeriodForm(request.GET)
        if form.is_valid():
            start_date = form.cleaned_data["start_date"]
            end_date = form.cleaned_data["end_date"]
    else:
        form = ReportPeriodForm(
            initial={"start_date": start_date, "end_date": end_date}
        )

    # Daily points stay readable for about a quarter; beyond that the line
    # chart is grouped by week instead.
    group = "day" if (end_date - start_date).days <= 92 else "week"

    return render(
        request,
        "reports/dashboard.html",
        {
            "form": form,
            "start_date": start_date,
            "end_date": end_date,
            "group": group,
            "kinds": CHART_KINDS,
        },
    )


def _parse_date(value, fallback):
    """A yyyy-mm-dd query parameter, or the fallback when it is absent."""
    if not value:
        return fallback
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


@login_required
def chart_data_view(request):
    """Chart figures as JSON (FR-018, SAD v1.1 Section 4.3 Report API).

    GET /reports/chart-data/?kind=pie&from=...&to=...&group=day
    """
    default_start, default_end = month_bounds()
    start_date = _parse_date(request.GET.get("from"), default_start)
    end_date = _parse_date(request.GET.get("to"), default_end)

    if start_date is None or end_date is None:
        return JsonResponse(
            {"error": "Dates must be in yyyy-mm-dd format."}, status=422
        )

    group = request.GET.get("group", "day")
    if group not in GROUPINGS:
        return JsonResponse(
            {"error": f"Unknown grouping. Use one of: {', '.join(GROUPINGS)}."},
            status=400,
        )

    try:
        payload = chart_data(
            request.user,
            request.GET.get("kind", "pie"),
            start_date,
            end_date,
            group,
        )
    except UnknownChartKind:
        return JsonResponse(
            {"error": f"Unknown chart kind. Use one of: {', '.join(CHART_KINDS)}."},
            status=400,
        )
    except InvalidPeriod:
        return JsonResponse(
            {"error": "The start date must not be after the end date."},
            status=422,
        )

    return JsonResponse(payload)
