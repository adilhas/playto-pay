from rest_framework.views import APIView
from rest_framework.response import Response
from .services import get_merchant_balance


class BalanceView(APIView):
    def get(self, request):
        merchant = request.user.merchant
        balance = get_merchant_balance(merchant)

        return Response({"balance_paise": balance})
