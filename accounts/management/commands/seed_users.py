from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from faker import Faker
import random

from accounts.models import BankAccount
from ledger.models import LedgerEntry

fake = Faker()


class Command(BaseCommand):
    help = "Seed users with bank accounts and balance"

    def handle(self, *args, **kwargs):
        created = 0

        for i in range(100):
            username = fake.user_name() + str(i)

            if User.objects.filter(username=username).exists():
                continue

            # ✅ Create user
            user = User.objects.create_user(
                username=username,
                email=fake.email(),
                password="test1234",
            )

            merchant = user.merchant  # via signal

            # ✅ Create bank account
            bank = BankAccount.objects.create(
                merchant=merchant,
                account_number=str(random.randint(1000000000, 9999999999)),
                ifsc_code="TEST0001",
            )

            # ✅ Add balance (random between ₹500 – ₹5000)
            amount = random.randint(50000, 500000)  # in paise

            LedgerEntry.objects.create(
                merchant=merchant,
                amount_paise=amount,
                transaction_type="credit",
                reference_type="seed",
                reference_id=user.id,
            )

            self.stdout.write(
                self.style.SUCCESS(f"Created {username} | Balance: {amount / 100} ₹")
            )

            created += 1

        self.stdout.write(self.style.SUCCESS(f"\nTotal users created: {created}"))
