from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import *

urlpatterns = [
  path('dispatcher_dashboard_stats/',DispatcherDashboardAPIView.as_view(),name="dashboard_stats"),
  path('delivery_rider/',DeliveryRiderAPIView.as_view(),name="delivery_rider")
]
