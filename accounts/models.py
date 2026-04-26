from django.contrib.auth.models import User
from django.db import models


class Merchant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="merchant")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


class BankAccount(models.Model):
    merchant = models.ForeignKey(
        Merchant, on_delete=models.CASCADE, related_name="bank_accounts"
    )
    account_number = models.CharField(max_length=20)
    ifsc_code = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.account_number} - {self.ifsc_code}"
