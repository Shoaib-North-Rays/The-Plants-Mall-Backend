import django_filters
from django.db.models import Q
from .models import Order

class OrderFilter(django_filters.FilterSet):
    query = django_filters.CharFilter(method="filter_query")
    start_date = django_filters.DateFilter(field_name="created_at", lookup_expr="gte")
    end_date = django_filters.DateFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = Order
        fields = ["status", "payment_status", "start_date", "end_date"]

    def filter_query(self, queryset, name, value):
        return queryset.filter(
            Q(order_number__icontains=value) |
            Q(shop__shop_name__icontains=value) |
            Q(order_taker__name__icontains=value)
        )
