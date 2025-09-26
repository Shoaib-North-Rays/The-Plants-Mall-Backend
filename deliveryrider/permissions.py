from rest_framework.permissions import BasePermission

class IsDeliveryOrAdmin(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        
        return user.role in ["delivery_rider", "admin"] or user.is_superuser
