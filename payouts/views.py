from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Payout
from accounts.models import BankAccount, Merchant
from ledger.models import LedgerEntry
from ledger.services import get_merchant_balance
from payouts.tasks import process_payout_task
from django.db import transaction, IntegrityError


class ListPayoutsView(APIView):
    def get(self, request):
        merchant = request.user.merchant

        payouts = Payout.objects.filter(merchant=merchant).order_by("-id")

        data = [
            {
                "id": p.id,
                "amount_paise": p.amount_paise,
                "status": p.status,
                "created_at": p.created_at,
            }
            for p in payouts
        ]

        return Response(data, status=status.HTTP_200_OK)


class CreatePayoutView(APIView):
    def post(self, request):
        idempotency_key = request.headers.get("Idempotency-Key")

        if not idempotency_key:
            return Response(
                {"error": "Idempotency-Key header required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        merchant = request.user.merchant
        amount = request.data.get("amount_paise")
        bank_account_id = request.data.get("bank_account_id")

        # ✅ Validate amount
        try:
            amount = int(amount)
            if amount <= 0:
                raise ValueError
        except (TypeError, ValueError):
            return Response(
                {"error": "Invalid amount"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ✅ Step 1: Fast idempotency check (no lock)
        existing_payout = Payout.objects.filter(
            merchant=merchant, idempotency_key=idempotency_key
        ).first()

        if existing_payout:
            return Response(
                {
                    "payout_id": existing_payout.id,
                    "status": existing_payout.status,
                },
                status=status.HTTP_200_OK,
            )

        error_response = None
        payout = None

        try:
            with transaction.atomic():
                # 🔒 Lock merchant row
                locked_merchant = Merchant.objects.select_for_update().get(
                    id=merchant.id
                )

                # Recalculate balance inside lock
                balance = get_merchant_balance(locked_merchant)

                if balance < amount:
                    error_response = Response(
                        {"error": "Insufficient balance"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                else:
                    # Validate bank account
                    try:
                        bank_account = BankAccount.objects.get(
                            id=bank_account_id, merchant=locked_merchant
                        )
                    except BankAccount.DoesNotExist:
                        error_response = Response(
                            {"error": "Invalid bank account"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    else:
                        # Create payout (idempotency protected by DB constraint)
                        payout = Payout.objects.create(
                            merchant=locked_merchant,
                            bank_account=bank_account,
                            amount_paise=amount,
                            status="pending",
                            idempotency_key=idempotency_key,
                        )
                        # HOLD funds via ledger
                        LedgerEntry.objects.create(
                            merchant=locked_merchant,
                            amount_paise=-amount,
                            transaction_type="debit",
                            reference_type="payout",
                            reference_id=payout.id,
                        )

                        def enqueue_payout_task(payout_id):
                            try:
                                process_payout_task.delay(payout_id)
                            except Exception as e:
                                # Log but NEVER crash request
                                print("Celery enqueue failed:", str(e))

                        payout_id = payout.id

                        transaction.on_commit(
                            lambda payout_id=payout_id: enqueue_payout_task(payout_id)
                        )
                        # payout_id = payout.id

                        # transaction.on_commit(
                        #     lambda: process_payout_task.delay(payout_id)
                        # )

        except IntegrityError:
            # Another request with same idempotency key won the race
            payout = Payout.objects.get(
                merchant=merchant, idempotency_key=idempotency_key
            )

        # ✅ Handle validation errors AFTER transaction
        if error_response:
            return error_response

        # ✅ Always return SAME response format (idempotency-safe)
        return Response(
            {
                "payout_id": payout.id,
                "status": payout.status,
            },
            status=status.HTTP_200_OK,
        )
