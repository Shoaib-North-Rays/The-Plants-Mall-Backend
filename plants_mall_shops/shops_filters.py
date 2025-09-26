import django_filters
from .models import Shop

class ShopFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=Shop.SHOP_STATUS)
    size = django_filters.ChoiceFilter(choices=Shop.SIZE_CHOICES)
    category = django_filters.NumberFilter(field_name="category__id")
    registered_by = django_filters.NumberFilter(field_name="registered_by__id")
    created_after = django_filters.DateFilter(field_name="created_at", lookup_expr="gte")
    created_before = django_filters.DateFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = Shop
        fields = [
            "status",
            "size",
            "category",
            "registered_by",
            "created_after",
            "created_before",
        ]
