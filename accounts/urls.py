from django.urls import path
from .views import MeView, BankAccountCreateView

urlpatterns = [
    path("me/", MeView.as_view()),
    path("bank-accounts/", BankAccountCreateView.as_view()),
]
