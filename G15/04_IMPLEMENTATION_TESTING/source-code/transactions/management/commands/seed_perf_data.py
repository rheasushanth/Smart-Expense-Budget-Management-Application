"""Seed the load-test dataset for TC-PERF-01 (NFR-001).

Creates one performance user holding 10,000 expense transactions spread
over a year, plus budgets for the report to summarise. Separate from
seed_demo so the demo data stays small and readable.
"""

import random
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction as db_transaction

from accounts.models import User
from budgets.models import Budget
from categories.models import Category
from transactions.models import Transaction

PERF_EMAIL = "perf@example.com"
CATEGORIES = ("Food", "Transport", "Shopping", "Bills", "Entertainment")


class Command(BaseCommand):
    help = "Seed the TC-PERF-01 load-test dataset (NFR-001)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=10_000,
            help="Number of transactions to create (default 10000).",
        )
        parser.add_argument(
            "--password",
            default=None,
            help=(
                "Password for the load-test user. Required the first time, "
                "so that no password is ever hard-coded in the repository."
            ),
        )

    @db_transaction.atomic
    def handle(self, *args, **options):
        count = options["count"]
        password = options["password"]

        admin, _ = User.objects.get_or_create(
            email="perf-admin@example.com",
            defaults={"name": "Perf Admin", "role": User.Role.ADMINISTRATOR},
        )

        user, created = User.objects.get_or_create(
            email=PERF_EMAIL, defaults={"name": "Perf User"}
        )
        if password:
            user.set_password(password)
            user.save(update_fields=["password"])
        elif created:
            raise SystemExit(
                "Pass --password the first time so the load-test user can log in."
            )

        categories = []
        for name in CATEGORIES:
            category, _ = Category.objects.get_or_create(
                name=name,
                defaults={
                    "type": Category.CategoryType.EXPENSE,
                    "created_by": admin,
                },
            )
            categories.append(category)

        Transaction.objects.filter(user=user).delete()

        # A fixed seed keeps successive runs comparable, so a change in the
        # measured 95th percentile reflects the code and not the data.
        random.seed(1)
        today = date.today()
        rows = [
            Transaction(
                user=user,
                category=random.choice(categories),
                amount=Decimal(random.randrange(50, 5000)),
                type=Transaction.TransactionType.EXPENSE,
                date=today - timedelta(days=random.randrange(0, 365)),
                note="",
            )
            for _ in range(count)
        ]
        # bulk_create skips Model.save, which is only the FR-021 disabled
        # category guard; every category created above is active.
        Transaction.objects.bulk_create(rows, batch_size=1000)

        Budget.objects.filter(user=user).delete()
        month_start = today.replace(day=1)
        for category in categories[:3]:
            budget = Budget(
                user=user,
                category=category,
                period=Budget.Period.MONTHLY,
                start_date=month_start,
                limit_amount=Decimal("50000.00"),
            )
            budget.full_clean()
            budget.save()

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {count} transactions and 3 budgets for {PERF_EMAIL}."
            )
        )
