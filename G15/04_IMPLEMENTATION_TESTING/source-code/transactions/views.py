
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import ExpenseForm, IncomeForm


@login_required
def record_income(request):
    if request.method == "POST":
        form = IncomeForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.type = "Income"
            transaction.source = "Manual"
            transaction.save()
            return redirect("record_income")
    else:
        form = IncomeForm()

    return render(
        request,
        "transactions/record_income.html",
        {"form": form},
    )

@login_required
def record_expense(request):
    if request.method == "POST":
        form = ExpenseForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.type = "Expense"
            transaction.source = "Manual"
            transaction.save()
            return redirect("record_expense")
    else:
        form = ExpenseForm()

    return render(
        request,
        "transactions/record_expense.html",
        {"form": form},
    )
