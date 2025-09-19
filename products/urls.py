
from django.urls import path
from .views import *

urlpatterns = [
    path("products/", ProductListCreateAPIView.as_view(), name="product-list-create"),
    path("products/<int:id>/", ProductRetrieveUpdateDestroyAPIView.as_view(), name="product-detail"),
    path("products/voice-products/", ProductListForAi.as_view(), name="voice-products"),
    
]
