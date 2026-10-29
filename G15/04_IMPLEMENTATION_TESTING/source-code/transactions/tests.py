
from datetime import date
from decimal import Decimal
from urllib import response


from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from categories.models import Category
from transactions.models import Transaction
from transactions.forms import ExpenseForm, IncomeForm


class RecordIncomeTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            email="manogna@example.com",
            password="TestPassword123!",
            name="Test User",
        )
        self.category = Category.objects.create(
            name="Salary",
            type=Category.CategoryType.INCOME,
            is_active=True,
            created_by=self.user,
        )
        self.client.login(
            email="manogna@example.com",
            password="TestPassword123!",
        )

    def test_user_can_record_income(self):
        response = self.client.post(
            reverse("record_income"),
            {
                "amount": "25000.00",
                "category": self.category.pk,
                "date": date.today().isoformat(),
                "note": "Monthly salary",
            },
        )

        self.assertRedirects(response, reverse("record_income"))
        transaction = Transaction.objects.get(
            user=self.user,
            type=Transaction.TransactionType.INCOME,
        )
        self.assertEqual(transaction.amount, Decimal("25000.00"))
        self.assertEqual(transaction.category, self.category)
        self.assertEqual(transaction.note, "Monthly salary")
        self.assertEqual(transaction.source, "Manual")

    def test_income_page_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("record_income"))
        self.assertEqual(response.status_code, 302)

    def test_expense_category_cannot_be_used_for_income(self):
        expense_category = Category.objects.create(
            name="Groceries",
            type=Category.CategoryType.EXPENSE,
            is_active=True,
            created_by=self.user,
        )

        response = self.client.post(
            reverse("record_income"),
            {
                "amount": "100.00",
                "category": expense_category.pk,
                "date": date.today().isoformat(),
                "note": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            Transaction.objects.filter(
                user=self.user,
                category=expense_category,
                type=Transaction.TransactionType.INCOME,
            ).exists()
        )

class RecordExpenseTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            email="expense@example.com",
            password="TestPassword123!",
            name="Expense Test User",
        )
        self.category = Category.objects.create(
            name="Groceries",
            type=Category.CategoryType.EXPENSE,
            is_active=True,
            created_by=self.user,
        )
        self.client.login(
            email="expense@example.com",
            password="TestPassword123!",
        )

    def test_user_can_record_expense(self):
        response = self.client.post(reverse("record_expense"), {
            "amount": "500.00",
            "category": self.category.pk,
            "date": date.today().isoformat(),
            "note": "Groceries shopping",
        })

        self.assertRedirects(response, reverse("record_expense"))
        transaction = Transaction.objects.get(
            user=self.user,
            type=Transaction.TransactionType.EXPENSE,
        )
        self.assertEqual(transaction.amount, Decimal("500.00"))
        self.assertEqual(transaction.category, self.category)
        self.assertEqual(transaction.note, "Groceries shopping")
        self.assertEqual(transaction.source, "Manual")

    def test_expense_page_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("record_expense"))
        self.assertEqual(response.status_code, 302)

    def test_income_category_cannot_be_used_for_expense(self):
        income_category = Category.objects.create(
            name="Salary",
            type=Category.CategoryType.INCOME,
            is_active=True,
            created_by=self.user,
        )

        response = self.client.post(reverse("record_expense"), {
            "amount": "100.00",
            "category": income_category.pk,
            "date": date.today().isoformat(),
            "note": "",
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Transaction.objects.filter(
            user=self.user,
            category=income_category,
            type=Transaction.TransactionType.EXPENSE,
        ).exists())

class CategoryValidationTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            email="categorytest@example.com",
            password="TestPassword123!",
            name="Category Test User",
        )
        self.income_category = Category.objects.create(
            name="Test Salary",
            type=Category.CategoryType.INCOME,
            is_active=True,
            created_by=self.user,
        )
        self.expense_category = Category.objects.create(
            name="Test Food",
            type=Category.CategoryType.EXPENSE,
            is_active=True,
            created_by=self.user,
        )
        self.client.login(
            email="categorytest@example.com",
            password="TestPassword123!",
        )

    def test_income_requires_category(self):
        response = self.client.post(reverse("record_income"), {
            "amount": "1000.00",
            "category": "",
            "date": date.today().isoformat(),
            "note": "",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Transaction.objects.filter(
            user=self.user,
            type=Transaction.TransactionType.INCOME,
        ).exists())

    def test_expense_requires_category(self):
        response = self.client.post(reverse("record_expense"), {
            "amount": "100.00",
            "category": "",
            "date": date.today().isoformat(),
            "note": "",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Transaction.objects.filter(
            user=self.user,
            type=Transaction.TransactionType.EXPENSE,
        ).exists())

    def test_inactive_category_is_rejected(self):
        inactive_category = Category.objects.create(
            name="Inactive Food",
            type=Category.CategoryType.EXPENSE,
            is_active=False,
            created_by=self.user,
        )
        response = self.client.post(reverse("record_expense"), {
            "amount": "100.00",
            "category": inactive_category.pk,
            "date": date.today().isoformat(),
            "note": "",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Transaction.objects.filter(
            user=self.user,
            category=inactive_category,
        ).exists())
    def test_income_rejects_zero_amount(self):
        form = IncomeForm(data={
            "amount": "0",
            "category": self.income_category.pk,
            "date": date.today().isoformat(),
            "note": "",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("amount", form.errors)

    def test_income_rejects_negative_five_amount(self):
        form = IncomeForm(data={
            "amount": "-5",
            "category": self.income_category.pk,
            "date": date.today().isoformat(),
            "note": "",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("amount", form.errors)

    def test_expense_rejects_zero_amount(self):
        form = ExpenseForm(data={
            "amount": "0",
            "category": self.expense_category.pk,
            "date": date.today().isoformat(),
            "note": "",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("amount", form.errors)

    def test_expense_rejects_negative_five_amount(self):
        form = ExpenseForm(data={
            "amount": "-5",
            "category": self.expense_category.pk,
            "date": date.today().isoformat(),
            "note": "",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("amount", form.errors)


class EditDeleteTransactionTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            email="editdelete@example.com",
            password="TestPassword123!",
            name="Edit Delete User",
        )
        self.category = Category.objects.create(
            name="Groceries",
            type=Category.CategoryType.EXPENSE,
            is_active=True,
            created_by=self.user,
        )
        self.transaction = Transaction.objects.create(
            user=self.user,
            type=Transaction.TransactionType.EXPENSE,
            source="Manual",
            amount=Decimal("250.00"),
            category=self.category,
            date=date.today(),
            note="Original note",
        )
        self.client.login(
            email="editdelete@example.com",
            password="TestPassword123!",
        )

    def test_TC_TXN_04_user_can_edit_transaction(self):
        response = self.client.post(
            reverse(
                "edit_transaction",
                args=[self.transaction.txn_id],
            ),
            {
                "amount": "300.00",
                "category": self.category.pk,
                "date": date.today().isoformat(),
                "note": "Updated note",
            },
        )

        self.assertRedirects(response, reverse("record_expense"))
        self.transaction.refresh_from_db()
        self.assertEqual(self.transaction.amount, Decimal("300.00"))
        self.assertEqual(self.transaction.note, "Updated note")

    def test_user_can_view_delete_confirmation(self):
        response = self.client.get(
            reverse(
                "delete_transaction",
                args=[self.transaction.txn_id],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "transactions/delete_transaction.html",
        )

    def test_user_can_delete_transaction_with_post(self):
        response = self.client.post(
            reverse(
                "delete_transaction",
                args=[self.transaction.txn_id],
            )
        )

        self.assertRedirects(response, reverse("record_expense"))
        self.assertFalse(
            Transaction.objects.filter(
                txn_id=self.transaction.txn_id
            ).exists()
        )

    def test_user_cannot_edit_another_users_transaction(self):
        User = get_user_model()
        other_user = User.objects.create_user(
            email="anotheruser@example.com",
            password="TestPassword123!",
            name="Another User",
        )
        other_transaction = Transaction.objects.create(
            user=other_user,
            type=Transaction.TransactionType.EXPENSE,
            source="Manual",
            amount=Decimal("200.00"),
            category=self.category,
            date=date.today(),
            note="Private transaction",
        )

        response = self.client.get(
            reverse(
                "edit_transaction",
                args=[other_transaction.txn_id],
            )
        )

        self.assertEqual(response.status_code, 404)
        other_transaction.refresh_from_db()
        self.assertEqual(other_transaction.amount, Decimal("200.00"))



class CSVImportTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            email="csvimport@example.com",
            password="TestPassword123!",
            name="CSV Import User",
        )

        self.expense_category = Category.objects.create(
            name="Food",
            type=Category.CategoryType.EXPENSE,
            is_active=True,
            created_by=self.user,
        )
        self.income_category = Category.objects.create(
            name="Salary",
            type=Category.CategoryType.INCOME,
            is_active=True,
            created_by=self.user,
        )

        self.client.login(
            email="csvimport@example.com",
            password="TestPassword123!",
        )

    def test_TC_TXN_05_imports_seven_valid_and_reports_three_invalid_rows(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        csv_content = (
            "date,amount,type,category,note\n"
            "2026-10-01,250.00,Expense,Food,Lunch\n"
            "2026-10-02,500.00,Expense,Food,Groceries\n"
            "2026-10-03,20000.00,Income,Salary,Salary\n"
            "bad-date,100.00,Expense,Food,Bad date\n"
            "2026-10-05,-50.00,Expense,Food,Negative\n"
            "2026-10-06,100.00,Expense,,Missing category\n"
            "2026-10-07,120.00,Expense,Food,Transport\n"
            "2026-10-08,300.00,Expense,Food,Dinner\n"
            "2026-10-09,1000.00,Income,Salary,Bonus\n"
            "2026-10-10,150.00,Expense,Food,Snacks\n"
        )

        upload = SimpleUploadedFile(
            "transactions.csv",
            csv_content.encode("utf-8"),
            content_type="text/csv",
        )

        response = self.client.post(
            reverse("import_transactions"),
            {"csv_file": upload},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["imported"], 7)
        self.assertEqual(len(response.context["errors"]), 3)
        self.assertEqual(
            {item["row"] for item in response.context["errors"]},
            {5, 6, 7},
        )
        self.assertEqual(
            Transaction.objects.filter(user=self.user).count(),
            7,
        )

    def test_import_page_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("import_transactions"))
        self.assertEqual(response.status_code, 302)

    def test_duplicate_csv_rows_are_skipped(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        csv_content = (
            "date,amount,type,category,note\n"
            "2026-10-11,100.00,Expense,Food,Bus\n"
            "2026-10-11,100.00,Expense,Food,Bus\n"
        )

        upload = SimpleUploadedFile(
            "duplicates.csv",
            csv_content.encode("utf-8"),
            content_type="text/csv",
        )

        response = self.client.post(
            reverse("import_transactions"),
            {"csv_file": upload},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["imported"], 1)
        self.assertEqual(
            Transaction.objects.filter(
                user=self.user,
                date="2026-10-11",
                amount=Decimal("100.00"),
                category=self.expense_category,
                note="Bus",
                source=Transaction.Source.CSV,
            ).count(),
            1,
        )
        self.assertEqual(len(response.context["errors"]), 1)
        self.assertIn("Duplicate", response.context["errors"][0]["reason"])
    def test_TC_SEC_03_rejects_csv_over_2mb(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        oversized_content = b"a" * (10 * 1024 * 1024)
        upload = SimpleUploadedFile(
            "oversized.csv",
            oversized_content,
            content_type="text/csv",
        )

        response = self.client.post(
            reverse("import_transactions"),
            {"csv_file": upload},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "File must be 2 MB or smaller.")
        self.assertEqual(
            Transaction.objects.filter(user=self.user).count(),
            0,
        )

    def test_TC_TXN_07_existing_and_in_file_duplicates_are_skipped(self):
        from datetime import date
        from django.core.files.uploadedfile import SimpleUploadedFile

        # Create a transaction that already exists in the database.
        Transaction.objects.create(
            user=self.user,
            date=date(2026, 10, 11),
            amount=Decimal("100.00"),
            category=self.expense_category,
            type=Transaction.TransactionType.EXPENSE,
            note="Bus",
        )

        csv_content = (
            "date,amount,type,category,note\n"
            "2026-10-11,100.00,Expense,Food,Bus\n"
            "2026-10-12,50.00,Expense,Food,Lunch\n"
            "2026-10-13,200.00,Income,Salary,Paycheck\n"
            "2026-10-12,50.00,Expense,Food,Lunch\n"
        )

        upload = SimpleUploadedFile(
            "tc_txn_07.csv",
            csv_content.encode("utf-8"),
            content_type="text/csv",
        )

        response = self.client.post(
            reverse("import_transactions"),
            {"csv_file": upload},
        )

        self.assertEqual(response.status_code, 200)

        # Two new rows should import; two duplicate rows should be reported.
        self.assertEqual(response.context["imported"], 2)
        self.assertEqual(len(response.context["errors"]), 2)

        reasons = [
            error["reason"] for error in response.context["errors"]
        ]
        self.assertTrue(
            all("Duplicate" in reason for reason in reasons)
        )

        # Exactly two CSV transactions should have been saved.
        self.assertEqual(
            Transaction.objects.filter(
                user=self.user,
                source=Transaction.Source.CSV,
            ).count(),
            2,
        )

        # The repeated Lunch transaction must exist only once.
        self.assertEqual(
            Transaction.objects.filter(
                user=self.user,
                date=date(2026, 10, 12),
                amount=Decimal("50.00"),
                note="Lunch",
                source=Transaction.Source.CSV,
            ).count(),
            1,
        )

        # The Paycheck transaction must also be saved.
        self.assertEqual(
            Transaction.objects.filter(
                user=self.user,
                date=date(2026, 10, 13),
                amount=Decimal("200.00"),
                note="Paycheck",
                source=Transaction.Source.CSV,
            ).count(),
            1,
        )
