from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import BudgetForm
from .models import Alert, Budget
from .services import budget_status


@login_required
def budget_list(request):
    """Budgets with spend to date, plus unread alerts.

    FR-012, FR-013; the alert panel is how FR-015 and FR-016 notify the user.
    """
    budgets = (
        Budget.objects.filter(user=request.user)
        .select_related("category")
        .order_by("-start_date")
    )
    rows = [budget_status(budget) for budget in budgets]
    alerts = (
        Alert.objects.filter(budget__user=request.user, is_read=False)
        .select_related("budget", "budget__category")
        .order_by("-triggered_on", "-alert_id")
    )
    return render(
        request,
        "budgets/budget_list.html",
        {"rows": rows, "alerts": alerts},
    )


@login_required
def alert_dismiss(request, alert_id):
    """Mark an alert as read (SRS Appendix B.6, is_read)."""
    alert = get_object_or_404(Alert, pk=alert_id, budget__user=request.user)
    if request.method == "POST":
        alert.is_read = True
        alert.save(update_fields=["is_read"])
    return redirect("budget_list")


@login_required
def budget_create(request):
    """Create a budget (FR-012)."""
    form = BudgetForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Budget created.")
        return redirect("budget_list")
    return render(request, "budgets/budget_form.html", {"form": form, "is_edit": False})


@login_required
def budget_edit(request, budget_id):
    """Edit a budget the signed-in user owns (FR-012)."""
    budget = get_object_or_404(Budget, pk=budget_id, user=request.user)
    form = BudgetForm(request.POST or None, instance=budget, user=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Budget updated.")
        return redirect("budget_list")
    return render(
        request,
        "budgets/budget_form.html",
        {"form": form, "is_edit": True, "budget": budget},
    )


@login_required
def budget_delete(request, budget_id):
    """Delete a budget the signed-in user owns (FR-012)."""
    budget = get_object_or_404(Budget, pk=budget_id, user=request.user)
    if request.method == "POST":
        budget.delete()
        messages.success(request, "Budget deleted.")
        return redirect("budget_list")
    return render(request, "budgets/budget_confirm_delete.html", {"budget": budget})
