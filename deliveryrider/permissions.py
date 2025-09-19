from rest_framework.permissions import BasePermission

class IsDeliveryRider(BasePermission):
    def has_permission(self, request, view):
        return getattr(request.user, "role", None) == "delivery_rider"