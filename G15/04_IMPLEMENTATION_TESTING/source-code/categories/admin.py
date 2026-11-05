from django.contrib import admin

from accounts.models import SecurityEvent
from accounts.security import log_security_event
from .models import Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("category_id", "name", "type", "is_active", "created_by")
    list_filter = ("type", "is_active")
    search_fields = ("name",)
    ordering = ("type", "name")

    def save_model(self, request, obj, form, change):
        old_is_active = None

        if change:
            old_is_active = (
                Category.objects.filter(pk=obj.pk)
                .values_list("is_active", flat=True)
                .first()
            )

        super().save_model(request, obj, form, change)

        if not change:
            event_type = SecurityEvent.EventType.CATEGORY_CREATED
            description = f"Administrator created category: {obj.name}."
        elif old_is_active != obj.is_active:
            event_type = SecurityEvent.EventType.CATEGORY_STATUS_CHANGED
            description = (
                f"Administrator changed category status: {obj.name}."
            )
        else:
            event_type = SecurityEvent.EventType.CATEGORY_UPDATED
            description = f"Administrator updated category: {obj.name}."

        log_security_event(
            event_type,
            description,
            request=request,
            user=request.user,
        )
