from django.urls import path

from . import views

urlpatterns = [
    path("", views.report_view, name="report"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("chart-data/", views.chart_data_view, name="chart_data"),
]
