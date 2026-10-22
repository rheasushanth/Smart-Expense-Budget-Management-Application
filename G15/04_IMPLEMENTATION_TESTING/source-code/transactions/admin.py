
from django.contrib import admin

from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "txn_id",
        "user",
        "type",
        "amount",
        "category",
        "date",
        "source",
    )
    list_filter = ("type", "source", "date")
    search_fields = ("user__email", "note")
