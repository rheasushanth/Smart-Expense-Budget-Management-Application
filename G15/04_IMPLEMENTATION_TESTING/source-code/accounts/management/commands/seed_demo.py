
from django.core.management.base import BaseCommand
from django.db import transaction as db_transaction

from accounts.models import User
from categories.models import Category


class Command(BaseCommand):
    help = "Create demo users and default expense/income categories."

    def handle(self, *args, **options):
        with db_transaction.atomic():
            # Create demo users without duplicating existing accounts.
            demo_users = [
                {
                    "email": "admin@example.com",
                    "name": "Demo Administrator",
                    "role": User.Role.ADMINISTRATOR,
                    "is_staff": True,
                    "is_superuser": True,
                },
                {
                    "email": "customer1@example.com",
                    "name": "Demo Customer One",
                    "role": User.Role.CUSTOMER,
                },
                {
                    "email": "customer2@example.com",
                    "name": "Demo Customer Two",
                    "role": User.Role.CUSTOMER,
                },
            ]

            created_users = {}

            for data in demo_users:
                email = data["email"]
                defaults = {
                    key: value
                    for key, value in data.items()
                    if key != "email"
                }

                user, created = User.objects.get_or_create(
                    email=email,
                    defaults=defaults,
                )

                if created:
                    user.set_unusable_password()
                    user.save(update_fields=["password"])
                    self.stdout.write(
                        self.style.SUCCESS(f"Created user: {email}")
                    )
                else:
                    self.stdout.write(f"User already exists: {email}")

                created_users[email] = user

            # Categories are created by the demo administrator.
            admin = created_users["admin@example.com"]

            categories = [
                ("Food", Category.CategoryType.EXPENSE),
                ("Transport", Category.CategoryType.EXPENSE),
                ("Shopping", Category.CategoryType.EXPENSE),
                ("Bills", Category.CategoryType.EXPENSE),
                ("Entertainment", Category.CategoryType.EXPENSE),
                ("Healthcare", Category.CategoryType.EXPENSE),
                ("Salary", Category.CategoryType.INCOME),
                ("Other Income", Category.CategoryType.INCOME),
            ]

            for name, category_type in categories:
                category, created = Category.objects.get_or_create(
                    name=name,
                    type=category_type,
                    defaults={
                        "created_by": admin,
                        "is_active": True,
                    },
                )

                if created:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Created category: {name} ({category_type})"
                        )
                    )
                else:
                    self.stdout.write(
                        f"Category already exists: {name} ({category_type})"
                    )

        self.stdout.write(
            self.style.SUCCESS(
                "Demo seeding completed. No usable passwords were assigned."
            )
        )
