from django.core.management.base import BaseCommand

from recurring.tasks import generate_due_transactions


class Command(BaseCommand):
    help = "Generate transactions for due recurring rules."

    def handle(self, *args, **options):
        results = generate_due_transactions()

        self.stdout.write(
            self.style.SUCCESS(
                "Recurring transaction generation completed. "
                f"Created: {results['created']}, "
                f"Skipped: {results['skipped']}, "
                f"Errors: {results['errors']}"
            )
        )