from django.contrib import admin
from django.contrib.auth import get_user_model

from .models import Category


User = get_user_model()


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("category_id", "name", "type", "is_active", "created_by")
    list_filter = ("type", "is_active")
    search_fields = ("name",)
    list_editable = ("is_active",)
    ordering = ("type", "name")


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """FR-022: Allow administrators to view registered users."""

    list_display = ("user_id", "name", "email", "role", "is_active", "date_joined")
    list_filter = ("role", "is_active")
    search_fields = ("name", "email")
    ordering = ("name", "email")
    readonly_fields = ("user_id", "date_joined", "last_login")
