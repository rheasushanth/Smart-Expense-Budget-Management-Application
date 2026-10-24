
"""
URL configuration for config project.
"""

from django.contrib import admin
from django.urls import include, path

from .views import home

urlpatterns = [
    path("", home, name="home"),
    path("budgets/", include("budgets.urls")),
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("transactions/", include("transactions.urls")),
]
