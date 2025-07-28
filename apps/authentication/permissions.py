from rest_framework.permissions import BasePermission

class RolePermission(BasePermission):
    """
    Checks if the user has at least one of the required roles.
    Usage:
        permission_classes = [RolePermission(['admin', 'staff'])]
    """
    def __init__(self, roles):
        self.allowed_roles = roles

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return any(role.name in self.allowed_roles for role in request.user.roles.all())
