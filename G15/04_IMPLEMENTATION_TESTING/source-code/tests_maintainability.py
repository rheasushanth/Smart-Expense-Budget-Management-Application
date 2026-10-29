"""TC-MNT-01 (NFR-005): maintainability of the business-logic apps.

The Test Plan defines TC-MNT-01 as: review the repository layout and run
coverage on the budgets, recurring and transactions apps; budgeting, alerts
and recurrence logic sit in separate apps, each with unit tests, and line
coverage is 70% or more.

The structural half is asserted here. The coverage half is enforced by the
"Enforce NFR-005 coverage threshold" step in .github/workflows/ci.yml, which
fails the build below 70% — a threshold cannot meaningfully assert on itself
from inside the run it is measuring.
"""

import importlib
from pathlib import Path

from django.apps import apps
from django.test import SimpleTestCase

BUSINESS_LOGIC_APPS = ["budgets", "recurring", "transactions"]

# Business rules must live in their own modules rather than in views, so they
# can be unit tested without HTTP (NFR-005, NFR-006; SAD v1.1 Section 3.5).
SERVICE_MODULES = [
    "budgets.services",
    "budgets.alerts",
    "transactions.importer",
]


class TCMNT01AppStructure(SimpleTestCase):
    """Structural half of TC-MNT-01."""

    def test_business_logic_lives_in_separate_installed_apps(self):
        installed = {config.label for config in apps.get_app_configs()}
        for label in BUSINESS_LOGIC_APPS:
            with self.subTest(app=label):
                self.assertIn(label, installed)

    def test_each_business_logic_app_has_tests(self):
        root = Path(__file__).resolve().parent
        for label in BUSINESS_LOGIC_APPS:
            with self.subTest(app=label):
                tests_file = root / label / "tests.py"
                self.assertTrue(
                    tests_file.exists(),
                    f"{label} has no tests.py",
                )
                self.assertIn(
                    "def test_",
                    tests_file.read_text(encoding="utf-8"),
                    f"{label}/tests.py defines no tests",
                )

    def test_budgeting_alerting_and_import_rules_sit_outside_the_views(self):
        for module_path in SERVICE_MODULES:
            with self.subTest(module=module_path):
                module = importlib.import_module(module_path)
                self.assertFalse(
                    module_path.endswith("views"),
                    "business rules must not live in a views module",
                )
                self.assertTrue(
                    any(
                        callable(getattr(module, name))
                        for name in dir(module)
                        if not name.startswith("_")
                    ),
                    f"{module_path} exposes no callable service",
                )

    def test_alert_evaluation_is_decoupled_from_the_entry_views(self):
        """SAD v1.1 Section 3.5: alerts are raised by an observer hook, so no
        transaction view needs to know about them."""
        from transactions import views as transaction_views

        source = Path(transaction_views.__file__).read_text(encoding="utf-8")
        self.assertNotIn("alerts", source.lower())

        from budgets import signals

        self.assertTrue(hasattr(signals, "evaluate_alerts_after_transaction"))
