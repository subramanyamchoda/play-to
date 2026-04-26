import uuid
import threading

from django.test import TransactionTestCase
from rest_framework.test import APIClient

from .models import (
    Merchant,
    BankAccount,
    LedgerEntry,
    Payout
)


class ConcurrencyTest(TransactionTestCase):
    """
    Use TransactionTestCase instead of TestCase
    because real concurrent DB locking must be tested
    outside Django's wrapped transaction behavior.
    """

    reset_sequences = True

    def setUp(self):
        self.merchant = Merchant.objects.create(
            name="Rahul",
            email="rahul@test.com"
        )

        self.bank = BankAccount.objects.create(
            merchant=self.merchant,
            holder_name="Rahul",
            account_number="123456",
            ifsc="HDFC001"
        )

        # ₹100 balance
        LedgerEntry.objects.create(
            merchant=self.merchant,
            entry_type="credit",
            amount_paise=10000
        )

        self.results = []

    def make_request(self):
        client = APIClient()

        response = client.post(
            "/api/v1/payouts",
            {
                "merchant_id": self.merchant.id,
                "amount_paise": 6000,   # ₹60
                "bank_account_id": self.bank.id
            },
            format="json",
            HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4())
        )

        self.results.append(response.status_code)

    def test_only_one_should_succeed(self):
        t1 = threading.Thread(target=self.make_request)
        t2 = threading.Thread(target=self.make_request)

        t1.start()
        t2.start()

        t1.join()
        t2.join()

        # Only one payout row should be created
        self.assertEqual(Payout.objects.count(), 1)

        # One success, one failure
        self.assertEqual(self.results.count(201), 1)
        self.assertEqual(self.results.count(400), 1)


class IdempotencyTest(TransactionTestCase):

    reset_sequences = True

    def setUp(self):
        self.client = APIClient()

        self.merchant = Merchant.objects.create(
            name="Aman",
            email="aman@test.com"
        )

        self.bank = BankAccount.objects.create(
            merchant=self.merchant,
            holder_name="Aman",
            account_number="22222",
            ifsc="ICICI01"
        )

        LedgerEntry.objects.create(
            merchant=self.merchant,
            entry_type="credit",
            amount_paise=50000
        )  # ₹500

    def test_same_key_no_duplicate(self):
        key = str(uuid.uuid4())

        payload = {
            "merchant_id": self.merchant.id,
            "amount_paise": 10000,   # ₹100
            "bank_account_id": self.bank.id
        }

        r1 = self.client.post(
            "/api/v1/payouts",
            payload,
            format="json",
            HTTP_IDEMPOTENCY_KEY=key
        )

        r2 = self.client.post(
            "/api/v1/payouts",
            payload,
            format="json",
            HTTP_IDEMPOTENCY_KEY=key
        )

        # Only one payout created
        self.assertEqual(Payout.objects.count(), 1)

        # Same payout returned
        self.assertEqual(r1.data["id"], r2.data["id"])

        # First call create, second call replay
        self.assertEqual(r1.status_code, 201)
        self.assertEqual(r2.status_code, 200)