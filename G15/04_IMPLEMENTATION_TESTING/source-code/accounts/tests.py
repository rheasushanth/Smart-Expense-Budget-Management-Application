
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from categories.models import Category
from transactions.models import Transaction
from budgets.models import Budget, Alert
from recurring.models import RecurringRule


class ProjectSetupTest(TestCase):
    def test_all_six_domain_models_are_available(self):
        """TC-MNT-01: Verify all six required domain models exist."""
        required_models = [
            User,
            Category,
            Transaction,
            Budget,
            RecurringRule,
            Alert,
        ]

        for model in required_models:
            with self.subTest(model=model.__name__):
                self.assertTrue(hasattr(model, "objects"))
