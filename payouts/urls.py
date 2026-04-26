from django.urls import path
from .views import CreatePayoutView

urlpatterns = [
    path("", CreatePayoutView.as_view()),
]
