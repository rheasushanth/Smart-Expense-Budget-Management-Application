from django.urls import path

from . import views

urlpatterns = [
    path("income/", views.record_income, name="record_income"),
    path("expense/", views.record_expense, name="record_expense"),
    path("<int:txn_id>/edit/", views.edit_transaction, name="edit_transaction"),
    path("<int:txn_id>/delete/", views.delete_transaction, name="delete_transaction"),
    path("import/", views.import_csv_transactions, name="import_transactions"),
]