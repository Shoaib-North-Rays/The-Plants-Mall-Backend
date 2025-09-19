from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/api/', include('Authentication.urls')), 
    path('admin_operations/api/',include('admin_operations.urls')),
    path('dispatcher/api/',include('dispatcher.urls')),
    path('deliveryrider/api/',include('deliveryrider.urls')),
    path('plants-mall-shops/api/', include('plants_mall_shops.urls')),
    path('plants-mall-products/api/', include('products.urls')),
    path('plants-mall-orders/api/', include('orders.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
if settings.DEBUG:   
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)