from django.urls import path
from .views import (
    CreatePayoutAPIView,
    DashboardAPIView,
    PayoutListAPIView
)

urlpatterns = [
    path("v1/payouts", CreatePayoutAPIView.as_view()),
    path("v1/dashboard", DashboardAPIView.as_view()),
    path("v1/payouts/history", PayoutListAPIView.as_view()),
]