from django.db import models
from accounts.models import Merchant


class LedgerEntry(models.Model):
    TRANSACTION_TYPES = (
        ("credit", "Credit"),
        ("debit", "Debit"),
    )

    merchant = models.ForeignKey(
        Merchant, on_delete=models.CASCADE, related_name="ledger_entries"
    )
    amount_paise = models.BigIntegerField()
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)

    reference_type = models.CharField(max_length=50)  # payout / payment
    reference_id = models.IntegerField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.merchant.id} - {self.amount_paise}"
