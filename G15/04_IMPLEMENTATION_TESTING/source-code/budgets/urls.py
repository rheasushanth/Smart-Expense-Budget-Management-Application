from django.urls import path

from . import views

urlpatterns = [
    path("", views.budget_list, name="budget_list"),
    path("new/", views.budget_create, name="budget_create"),
    path("<int:budget_id>/edit/", views.budget_edit, name="budget_edit"),
    path("<int:budget_id>/delete/", views.budget_delete, name="budget_delete"),
]
