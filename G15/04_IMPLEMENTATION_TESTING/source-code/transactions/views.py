
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import IncomeForm


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
