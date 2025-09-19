
from django.urls import path
from .views import *
from django.views.generic import TemplateView

urlpatterns = [
    path("shops/create/", ShopCreateAPIView.as_view(), name="shop-create"),
    path("shops/create/voice/", SpeechToTextShopRegistrationAPIView.as_view(), name="shop-create-with-voice"),
    path("shops/", ShopListAPIView.as_view(), name="shop-list"),
    path("shops/<int:id>/edit/", ShopUpdateAPIView.as_view(), name="shop-edit"),
    path("shops/nearby/", NearbyShopsAPIView.as_view(), name="nearby-shops"),
    path("update-locations/", UpdateLocationAPIView.as_view(), name="update-location"),
    path("staff-locations/", SalesmenLocationsAPIView.as_view(), name="salesmen-locations"),
    path("monitor/", TemplateView.as_view(template_name="tracking/map.html"), name="monitor"),
    path("show_staff/", TemplateView.as_view(template_name="tracking/show_staff_location.html"), name="monitor"),
    path("salesman_stats/stats/", shop_stats, name="shop-stats"),
]
