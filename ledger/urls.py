from django.urls import path
from .views import BalanceView, LedgerListView

urlpatterns = [
    path("balance/", BalanceView.as_view()),
    path("entries/", LedgerListView.as_view()),
]
