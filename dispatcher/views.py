from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils.timezone import now
from django.contrib.auth import get_user_model
from orders.models import Order
from django.db.models import Sum
from plants_mall_shops.models import Shop
from rest_framework import  permissions
from .permissions import IsDispatcher
from orders.models import Order
from rest_framework import generics
from .serializers import DeliveryRiderSerializer

User = get_user_model()



class DispatcherDashboardAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsDispatcher]

    def get(self, request):
        dispatcher = request.user  

         
        assigned_orders = Order.objects.filter(dispatcher=dispatcher)

        orders_today = assigned_orders.filter(created_at__date=now().date()).count()
        preparing = assigned_orders.filter(status="preparing").count()
        ready = assigned_orders.filter(status="ready").count()
 

        return Response({
            "dispatcher_id": dispatcher.id,
            "dispatcher_analytics": {
                "total_orders":assigned_orders.count(),
                "orders_today": orders_today,
                "preparing": preparing,
                "ready": ready,
                
            },
        })
class DeliveryRiderAPIView(generics.ListAPIView):
    serializer_class = DeliveryRiderSerializer
    permission_classes = [permissions.IsAuthenticated, IsDispatcher]

    def get_queryset(self):
        return User.objects.filter(role="delivery_rider", is_active=True)