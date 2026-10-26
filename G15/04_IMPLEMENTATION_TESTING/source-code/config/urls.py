
from django.contrib import admin
from django.urls import include, path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("transactions/", include("transactions.urls")),
    path("categories/", include("categories.urls")),
    path("budgets/", include("budgets.urls")),
    path("recurring/", include("recurring.urls")),
]
