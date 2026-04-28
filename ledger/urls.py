from django.urls import path
from .views import BalanceView, LedgerListView

urlpatterns = [
    path("balance/", BalanceView.as_view()),
    path("list/", LedgerListView.as_view()),
]
