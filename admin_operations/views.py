from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils.timezone import now
from django.contrib.auth import get_user_model
from orders.models import Order
from django.db.models import Sum
from plants_mall_shops.models import Shop
from rest_framework import generics, permissions, status
from .serializers import DispatcherSerializer,UserRoleSerializer
from django.utils import timezone
from datetime import timedelta
User = get_user_model()
class DashboardStatsAPIView(APIView):
    permission_classes = [permissions.IsAdminUser, permissions.IsAuthenticated]

    def get(self, request):
        active_salesmen_count = User.objects.filter(role="sales_man", is_active=True).count()
        orders_today = Order.objects.filter(created_at__date=now().date()).count()
        revenue_today = (
            Order.objects.filter(created_at__date=now().date())
            .aggregate(total=Sum("total_amount"))["total"]
            or 0
        )

        total_shops = Shop.objects.count()
        pending = Order.objects.filter(status="pending").count()
        ready = Order.objects.filter(status="ready").count()
        completed = Order.objects.filter(status="delivered").count()
        preparing = Order.objects.filter(status="preparing").count()
        cancelled = Order.objects.filter(status="cancelled").count()

        active_salesmen = [
            {
                "id": s.id,
                "name": s.name,
                "phone": s.phone,
                "shops_count": s.sales_man_shops.count(),
                "orders_count": Order.objects.filter(order_taker=s).count(),
                "status": "online" if s.last_activity and s.last_activity >= timezone.now() - timedelta(minutes=5) else "offline",
                "last_seen": s.last_activity,  # timestamp
            }
            for s in User.objects.filter(role="sales_man")  # adjust filter as per your role field
        ]

        return Response({
            "real_time_operations": {
                "active_salesmen": active_salesmen_count,
                "orders_today": orders_today,
                "revenue_today": revenue_today,
            },
            "shops": {
                "total": total_shops,
                "pending": pending,
                "ready": ready,
                "completed": completed,
                "preparing":preparing,
                "cancelled":cancelled,
            },
            "active_salesmen": active_salesmen,
        })
 


 

class DispatcherListAPIView(generics.ListAPIView):
    serializer_class = DispatcherSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return User.objects.filter(role="dispatcher", is_active=True)

class StaffUsersAPIView(generics.ListAPIView):
    serializer_class = UserRoleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return User.objects.filter(role__in=["sales_man", "delivery_rider", "dispatcher"])