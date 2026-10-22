
from django.urls import path

from . import views

urlpatterns = [
    path("income/", views.record_income, name="record_income"),
]
