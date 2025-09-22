from django.urls import path
from .views import OrderListCreateAPIView, OrderRetrieveUpdateDestroyAPIView,SpeechToTextAPIView

urlpatterns = [
    path('orders/', OrderListCreateAPIView.as_view(), name='order-list-create'),
    path('orders/<int:id>/', OrderRetrieveUpdateDestroyAPIView.as_view(), name='order-detail'),
    path("orders/speech-to-text/", SpeechToTextAPIView.as_view(), name="speech-to-text"), 

]
