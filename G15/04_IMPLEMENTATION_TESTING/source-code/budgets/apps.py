from django.apps import AppConfig


class BudgetsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'budgets'

    def ready(self):
        # Registers the post_save hook that raises budget alerts
        # (SAD v1.1 Section 3.5).
        from . import signals  # noqa: F401
