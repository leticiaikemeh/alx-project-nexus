from rest_framework.permissions import BasePermission, SAFE_METHODS
from .constants import Roles


def RolePermission(allowed_roles):
    """
    Factory for a role-based permission class.
    Usage:
        permission_classes = [RolePermission([Roles.ADMIN, Roles.ADMIN])]
    """
    class _RolePermission(BasePermission):
        def has_permission(self, request, view):
            if not request.user or not request.user.is_authenticated:
                return False
            return any(role.name in allowed_roles for role in request.user.roles.all())
    return _RolePermission


class IsAdminRole(BasePermission):
    """Allow access only to users with the 'admin' role."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_role(Roles.ADMIN)


class IsSelfOrAdmin(BasePermission):
    """Allow access to a user's own data or by an admin."""
    def has_object_permission(self, request, view, obj):
        return (
            request.user.is_authenticated and (
                obj == request.user or
                request.user.has_role(Roles.ADMIN)
            )
        )

class IsOwnerOrAdmin(BasePermission):
    """
    Object-level permission to only allow owners of an object or admins to access it.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return obj.user == request.user or request.user.is_staff
        return obj.user == request.user

class IsAdminOrReadOnly(BasePermission):
    """
    Allow anyone to read, only admins can write/delete.
    """
    def has_permission(self, request, view):
        return (
            request.method in SAFE_METHODS or 
            request.user and request.user.is_staff
        )

class CanShipOrders(BasePermission):
    """
    Only warehouse staff or admins can update order status to 'shipped' or 'delivered'.
    """
    def has_object_permission(self, request, view, obj):
        if request.method not in ['PATCH', 'PUT']:
            return True  # Allow read or delete

        if 'status' in request.data:
            new_status = request.data['status']
            if new_status in ['shipped', 'delivered']:
                return request.user.is_staff or getattr(request.user, 'role', '') == Roles.WAREHOUSE
        
        return True
