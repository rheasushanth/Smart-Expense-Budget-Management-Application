from django.urls import path

from . import views

urlpatterns = [
    path("", views.rule_list, name="rule_list"),
    path("new/", views.rule_create, name="rule_create"),
    path("<int:rule_id>/edit/", views.rule_edit, name="rule_edit"),
    path("<int:rule_id>/deactivate/", views.rule_deactivate, name="rule_deactivate"),
]
