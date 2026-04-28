from rest_framework.views import APIView
from rest_framework.response import Response
from .services import get_merchant_balance
from rest_framework import status

from .models import LedgerEntry


class LedgerListView(APIView):
    def get(self, request):
        merchant = request.user.merchant

        entries = LedgerEntry.objects.filter(merchant=merchant).order_by("-id")[:20]

        data = [
            {
                "id": e.id,
                "amount_paise": e.amount_paise,
                "type": "credit" if e.amount_paise > 0 else "debit",
                "reference_type": e.reference_type,
                "created_at": e.created_at,
            }
            for e in entries
        ]

        return Response(data, status=status.HTTP_200_OK)


class BalanceView(APIView):
    def get(self, request):
        merchant = request.user.merchant
        balance = get_merchant_balance(merchant)

        return Response({"balance_paise": balance})
