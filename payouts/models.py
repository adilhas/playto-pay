from django.db import models
from accounts.models import Merchant, BankAccount


class Payout(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    )

    merchant = models.ForeignKey(
        Merchant, on_delete=models.CASCADE, related_name="payouts"
    )

    bank_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE)

    amount_paise = models.BigIntegerField()

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.id} - {self.amount_paise} - {self.status}"
