from django.urls import path
from .views import CreatePayoutView, ListPayoutsView

urlpatterns = [
    path("", CreatePayoutView.as_view()),
    path("list/", ListPayoutsView.as_view()),
]
