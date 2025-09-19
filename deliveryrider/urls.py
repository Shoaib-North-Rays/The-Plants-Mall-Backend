
from django.urls import path
from .views import *

urlpatterns = [
  path('delivery_rider_dashboard_stats/',DeliveryRiderDashboardAPIView.as_view(),name="delivery_rider_dashboard_stats"),
  # path('delivery_rider/',DeliveryRiderAPIView.as_view(),name="delivery_rider")
]
