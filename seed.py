import django
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth.models import User
from ledger.models import LedgerEntry


def run():
    for i in range(1, 4):
        user = User.objects.create(username=f"user{i}")
        merchant = user.merchant

        LedgerEntry.objects.create(
            merchant=merchant,
            amount_paise=100000,  # ₹1000
            transaction_type="credit",
            reference_type="seed",
            reference_id=i,
        )

        print(f"Seeded merchant {merchant.id}")


if __name__ == "__main__":
    run()
