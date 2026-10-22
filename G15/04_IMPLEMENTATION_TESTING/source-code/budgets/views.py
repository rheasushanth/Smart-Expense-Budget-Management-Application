from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import BudgetForm
from .models import Budget


@login_required
def budget_list(request):
    """List the signed-in user's budgets (FR-012)."""
    budgets = (
        Budget.objects.filter(user=request.user)
        .select_related("category")
        .order_by("-start_date")
    )
    return render(request, "budgets/budget_list.html", {"budgets": budgets})


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
