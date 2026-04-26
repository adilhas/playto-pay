from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Payout
from accounts.models import BankAccount
from ledger.models import LedgerEntry
from ledger.services import get_merchant_balance

from django.db import transaction
from accounts.models import Merchant


class CreatePayoutView(APIView):
    def post(self, request):
        merchant_id = request.user.merchant.id

        amount = int(request.data.get("amount_paise"))
        bank_account_id = request.data.get("bank_account_id")

        with transaction.atomic():
            # 🔒 LOCK merchant row
            merchant = Merchant.objects.select_for_update().get(id=merchant_id)

            # Recalculate balance inside lock
            balance = get_merchant_balance(merchant)

            if balance < amount:
                return Response(
                    {"error": "Insufficient balance"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Validate bank account
            try:
                bank_account = BankAccount.objects.get(
                    id=bank_account_id, merchant=merchant
                )
            except BankAccount.DoesNotExist:
                return Response(
                    {"error": "Invalid bank account"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Create payout
            payout = Payout.objects.create(
                merchant=merchant,
                bank_account=bank_account,
                amount_paise=amount,
                status="pending",
            )

            # HOLD funds
            LedgerEntry.objects.create(
                merchant=merchant,
                amount_paise=-amount,
                transaction_type="debit",
                reference_type="payout",
                reference_id=payout.id,
            )

        return Response(
            {"payout_id": payout.id, "status": payout.status},
            status=status.HTTP_201_CREATED,
        )
