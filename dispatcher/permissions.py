from rest_framework.permissions import BasePermission

class IsDispatcherOrAdmin(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        
        return user.role in ["dispatcher", "admin"] or user.is_superuser
