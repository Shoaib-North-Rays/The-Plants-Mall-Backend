
from django.urls import path
from .views import *
urlpatterns = [
    path("products/",create_product, name="product-list-create"),
    path("products/<int:pk>/update/",update_product, name="update-product"),
    path("all_products/",list_products, name="list_products"),
    path("products/voice-products/", ProductListForAi.as_view(), name="voice-products"),
    path("products/<int:pk>/detail/",retrieve_product, name="update-product"),
 
    
]
