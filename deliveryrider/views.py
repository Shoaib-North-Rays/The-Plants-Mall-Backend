from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils.timezone import now
from django.contrib.auth import get_user_model
from orders.models import Order
from django.db.models import Sum
from plants_mall_shops.models import Shop
from rest_framework import  permissions
from .permissions import IsDeliveryRider
from orders.models import Order
from rest_framework import generics
 

User = get_user_model()



class DeliveryRiderDashboardAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated,  IsDeliveryRider]

    def get(self, request):
        delivery_ride = request.user  

         
        assigned_orders = Order.objects.filter(delivery_rider=delivery_ride)

        orders_today = assigned_orders.filter(created_at__date=now().date()).count()
        delivered = assigned_orders.filter(status="delivered").count()
        ready = assigned_orders.filter(status="ready").count()
 

        return Response({
            "delivery_ride_id": delivery_ride.id,
            "delivery_ride_analytics": {
                "total_orders":assigned_orders.count(),
                "orders_today": orders_today,
                "delivered": delivered,
                "ready": ready,
                
            },
        })