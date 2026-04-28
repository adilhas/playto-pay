import os
import django
from accounts.models import BankAccount
from ledger.models import LedgerEntry
from django.contrib.auth.models import User


django.setup()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")


DEFAULT_USERS = 100
DEFAULT_PASSWORD = "Dummy@123"
DEFAULT_IFSC = "HDFC0001234"


def run(total_users: int = DEFAULT_USERS, password: str = DEFAULT_PASSWORD):
    """Seed dummy users with merchant balance + bank account for local testing."""
    for i in range(1, total_users + 1):
        username = f"dummyuser{i}"
        user, created = User.objects.get_or_create(username=username)

        if created:
            user.set_password(password)
            user.save(update_fields=["password"])

        merchant = user.merchant

        BankAccount.objects.get_or_create(
            merchant=merchant,
            account_number=f"100000000{i:03d}",
            ifsc_code=DEFAULT_IFSC,
        )

        LedgerEntry.objects.get_or_create(
            merchant=merchant,
            amount_paise=100000,  # ₹1000
            transaction_type="credit",
            reference_type="seed",
            reference_id=i,
        )

        status = "created" if created else "exists"
        print(
            f"{status}: username={username} password={password} merchant_id={merchant.id}"
        )


if __name__ == "__main__":
    run()
