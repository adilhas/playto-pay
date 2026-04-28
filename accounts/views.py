from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import BankAccount


class MeView(APIView):
    def get(self, request):
        merchant = request.user.merchant

        return Response({"user": request.user.username, "merchant_id": merchant.id})


class BankAccountCreateView(APIView):
    def get(self, request):
        merchant = request.user.merchant

        accounts = BankAccount.objects.filter(merchant=merchant)

        data = [
            {
                "id": acc.id,
                "account_number": acc.account_number,
                "ifsc_code": acc.ifsc_code,
            }
            for acc in accounts
        ]

        return Response(data, status=status.HTTP_200_OK)

    def post(self, request):
        merchant = request.user.merchant

        bank = BankAccount.objects.create(
            merchant=merchant,
            account_number=request.data.get("account_number"),
            ifsc_code=request.data.get("ifsc_code"),
        )

        return Response(
            {
                "id": bank.id,
                "account_number": bank.account_number,
                "ifsc_code": bank.ifsc_code,
            },
            status=status.HTTP_201_CREATED,
        )


# class BankAccountCreateView(APIView):
#     def post(self, request):
#         merchant = request.user.merchant

#         bank = BankAccount.objects.create(
#             merchant=merchant,
#             account_number=request.data.get("account_number"),
#             ifsc_code=request.data.get("ifsc_code"),
#         )

#         return Response(
#             {
#                 "id": bank.id,
#                 "account_number": bank.account_number,
#                 "ifsc_code": bank.ifsc_code,
#             },
#             status=status.HTTP_201_CREATED,
#         )
