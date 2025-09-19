from rest_framework.permissions import BasePermission

class IsDispatcher(BasePermission):
    def has_permission(self, request, view):
        return getattr(request.user, "role", None) == "dispatcher"