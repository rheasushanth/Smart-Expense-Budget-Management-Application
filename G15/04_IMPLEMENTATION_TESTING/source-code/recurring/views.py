from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import RecurringRuleForm
from .models import RecurringRule


@login_required
def rule_list(request):
    """List the signed-in user's recurring rules (FR-019)."""
    rules = (
        RecurringRule.objects.filter(user=request.user)
        .select_related("category")
        .order_by("-is_active", "next_run_date")
    )
    return render(request, "recurring/rule_list.html", {"rules": rules})


@login_required
def rule_create(request):
    """Configure a recurring rule (FR-019)."""
    form = RecurringRuleForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Recurring rule created.")
        return redirect("rule_list")
    return render(request, "recurring/rule_form.html", {"form": form, "is_edit": False})


@login_required
def rule_edit(request, rule_id):
    """Edit a recurring rule the signed-in user owns (FR-019)."""
    rule = get_object_or_404(RecurringRule, pk=rule_id, user=request.user)
    form = RecurringRuleForm(request.POST or None, instance=rule, user=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Recurring rule updated.")
        return redirect("rule_list")
    return render(
        request,
        "recurring/rule_form.html",
        {"form": form, "is_edit": True, "rule": rule},
    )


@login_required
def rule_deactivate(request, rule_id):
    """Stop a rule generating further transactions (FR-019).

    The rule is kept rather than deleted, so the history of what it already
    generated stays intact.
    """
    rule = get_object_or_404(RecurringRule, pk=rule_id, user=request.user)
    if request.method == "POST":
        rule.deactivate()
        messages.success(request, "Recurring rule deactivated.")
        return redirect("rule_list")
    return render(request, "recurring/rule_confirm_deactivate.html", {"rule": rule})
