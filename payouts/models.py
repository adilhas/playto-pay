from django.db import models
from accounts.models import Merchant, BankAccount


class Payout(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    )

    def __str__(self):
        return f"{self.id} - {self.amount_paise} - {self.status}"

    class Meta:
        unique_together = ("merchant", "idempotency_key")

    merchant = models.ForeignKey(
        Merchant, on_delete=models.CASCADE, related_name="payouts"
    )

    idempotency_key = models.CharField(max_length=255)
    bank_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE)

    amount_paise = models.BigIntegerField()

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    created_at = models.DateTimeField(auto_now_add=True)

    retry_count = models.IntegerField(default=0)
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    ALLOWED_TRANSITIONS = {
        "pending": ["processing"],
        "processing": ["completed", "failed"],
        "completed": [],
        "failed": [],
    }

    def transition_to(self, new_status):
        allowed = self.ALLOWED_TRANSITIONS.get(self.status, [])

        if new_status not in allowed:
            raise ValueError(f"Invalid transition: {self.status} → {new_status}")

        self.status = new_status
        self.save(update_fields=["status"])
