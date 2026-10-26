from django.contrib import admin
from .models import Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("category_id", "name", "type", "is_active", "created_by")
    list_filter = ("type", "is_active")
    search_fields = ("name",)
    list_editable = ("is_active",)
    ordering = ("type", "name")
