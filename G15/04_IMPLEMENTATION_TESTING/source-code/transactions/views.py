
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ExpenseForm, IncomeForm
from .models import Transaction


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


@login_required
def edit_transaction(request, txn_id):
    transaction = get_object_or_404(
        Transaction,
        txn_id=txn_id,
        user=request.user,
        source="Manual",
    )

    form_class = (
        IncomeForm
        if transaction.type == "Income"
        else ExpenseForm
    )

    if request.method == "POST":
        form = form_class(request.POST, instance=transaction)
        if form.is_valid():
            updated_transaction = form.save(commit=False)
            updated_transaction.user = request.user
            updated_transaction.type = transaction.type
            updated_transaction.source = transaction.source
            updated_transaction.save()
            return redirect(
                "record_income"
                if transaction.type == "Income"
                else "record_expense"
            )
    else:
        form = form_class(instance=transaction)

    return render(
        request,
        "transactions/edit_transaction.html",
        {"form": form, "transaction": transaction},
    )


@login_required
def delete_transaction(request, txn_id):
    transaction = get_object_or_404(
        Transaction,
        txn_id=txn_id,
        user=request.user,
        source="Manual",
    )

    if request.method == "POST":
        transaction_type = transaction.type
        transaction.delete()
        return redirect(
            "record_income"
            if transaction_type == "Income"
            else "record_expense"
        )

    return render(
        request,
        "transactions/delete_transaction.html",
        {"transaction": transaction},
    )
