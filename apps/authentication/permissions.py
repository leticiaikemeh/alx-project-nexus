from rest_framework.permissions import BasePermission


def RolePermission(allowed_roles):
    """
    Factory for a role-based permission class.
    Usage:
        permission_classes = [RolePermission(['admin', 'staff'])]
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
        return request.user.is_authenticated and request.user.has_role('admin')


class IsSelfOrAdmin(BasePermission):
    """Allow access to a user's own data or by an admin."""
    def has_object_permission(self, request, view, obj):
        return (
            request.user.is_authenticated and (
                obj == request.user or
                request.user.has_role('admin')
            )
        )
