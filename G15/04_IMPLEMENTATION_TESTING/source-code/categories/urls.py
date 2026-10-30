
from django.urls import path

from . import views

app_name = "categories"

urlpatterns = [
    path("", views.category_list, name="list"),
    path("users/", views.user_list, name="user_list"),
    path("add/", views.category_add, name="add"),
    path("<int:category_id>/edit/", views.category_edit, name="edit"),
    path("<int:category_id>/disable/", views.category_disable, name="disable"),
    path("<int:category_id>/enable/", views.category_enable, name="enable"),
]
