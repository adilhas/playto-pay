import threading
from django.test import TransactionTestCase, TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from ledger.models import LedgerEntry
from accounts.models import BankAccount


# ⚔️ Concurrency Test
class ConcurrencyTest(TransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="pass")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.merchant = self.user.merchant

        # Create bank account
        self.bank = BankAccount.objects.create(
            merchant=self.merchant,
            account_number="123",
            ifsc_code="TEST0001",
        )

        # Add balance
        LedgerEntry.objects.create(
            merchant=self.merchant,
            amount_paise=50000,
            transaction_type="credit",
            reference_type="test",
            reference_id=1,
        )

    def make_request(self, results, index):
        response = self.client.post(
            "/api/v1/payouts/",
            {
                "amount_paise": 50000,
                "bank_account_id": self.bank.id,
            },
            format="json",
            HTTP_IDEMPOTENCY_KEY=f"key-{index}",
        )
        results[index] = response.json()

    def test_concurrent_payout(self):
        results = [None, None]

        t1 = threading.Thread(target=self.make_request, args=(results, 0))
        t2 = threading.Thread(target=self.make_request, args=(results, 1))

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        # Only one should succeed
        success_count = sum(1 for r in results if "payout_id" in r)

        self.assertEqual(success_count, 1)


# 🔁 Idempotency Test
class IdempotencyTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser2", password="pass")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.merchant = self.user.merchant

        # Create bank account
        self.bank = BankAccount.objects.create(
            merchant=self.merchant,
            account_number="123",
            ifsc_code="TEST0001",
        )

        # Add balance
        LedgerEntry.objects.create(
            merchant=self.merchant,
            amount_paise=50000,
            transaction_type="credit",
            reference_type="test",
            reference_id=1,
        )

    def test_idempotency(self):
        key = "same-key"

        response1 = self.client.post(
            "/api/v1/payouts/",
            {
                "amount_paise": 10000,
                "bank_account_id": self.bank.id,
            },
            format="json",
            HTTP_IDEMPOTENCY_KEY=key,
        )

        response2 = self.client.post(
            "/api/v1/payouts/",
            {
                "amount_paise": 10000,
                "bank_account_id": self.bank.id,
            },
            format="json",
            HTTP_IDEMPOTENCY_KEY=key,
        )

        self.assertEqual(response1.json(), response2.json())
