# apps/core/views.py
from __future__ import annotations

from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse

from .models import Address, AuditLog
from .serializers import AddressSerializer, AuditLogListSerializer, AuditLogDetailSerializer
from apps.authentication.permissions import IsOwnerOrAdmin
from apps.authentication.constants import Roles


@extend_schema_view(
    list=extend_schema(
        summary="List my addresses",
        description="Returns addresses belonging to the authenticated user.",
        tags=["Core: Addresses"],
        responses={200: OpenApiResponse(
            response=AddressSerializer(many=True))},
    ),
    retrieve=extend_schema(
        summary="Retrieve an address",
        tags=["Core: Addresses"],
        responses={200: OpenApiResponse(
            response=AddressSerializer), 404: OpenApiResponse(description="Not found")},
    ),
    create=extend_schema(
        summary="Create an address",
        tags=["Core: Addresses"],
        request=AddressSerializer,
        responses={201: OpenApiResponse(response=AddressSerializer)},
    ),
    update=extend_schema(
        summary="Update an address",
        tags=["Core: Addresses"],
        responses={200: OpenApiResponse(response=AddressSerializer)},
    ),
    partial_update=extend_schema(
        summary="Partially update an address",
        tags=["Core: Addresses"],
        responses={200: OpenApiResponse(response=AddressSerializer)},
    ),
    destroy=extend_schema(
        summary="Delete an address",
        tags=["Core: Addresses"],
        responses={204: OpenApiResponse(description="Deleted")},
    ),
)
class AddressViewSet(viewsets.ModelViewSet):
    """
    Address API.
    Users manage their own addresses; admins can access all.
    """
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    queryset = Address.objects.none()

    def get_queryset(self):
        # Avoid touching request.user during schema generation
        if getattr(self, "swagger_fake_view", False):
            return Address.objects.none()

        user = self.request.user
        qs = Address.objects.select_related('user')
        is_admin = (
            getattr(user, 'is_staff', False)
            or getattr(user, 'is_superuser', False)
            or getattr(user, 'has_role', lambda *_: False)(Roles.ADMIN)
        )
        return qs if is_admin else qs.filter(user=user)


@extend_schema_view(
    list=extend_schema(
        summary="List audit logs (scoped)",
        description=(
            "Returns audit logs.\n\n"
            "- **Admins** (is_staff/superuser/role=ADMIN): see all logs.\n"
            "- **Users**: see only logs related to their own actions/resources (adjust filter as needed)."
        ),
        tags=["Core: Audit Logs"],
        responses={200: OpenApiResponse(
            response=AuditLogListSerializer(many=True))},
    ),
    retrieve=extend_schema(
        summary="Retrieve an audit log entry",
        tags=["Core: Audit Logs"],
        responses={200: OpenApiResponse(
            response=AuditLogDetailSerializer), 404: OpenApiResponse(description="Not found")},
    ),
)
class AuditLogViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    Read-only Audit Log API.
    Intended for observability and compliance surfaces. Mutations are disabled.
    """
    permission_classes = [IsAuthenticated]
    queryset = AuditLog.objects.none()

    def get_queryset(self):
        # NEW: short-circuit during schema generation
        if getattr(self, "swagger_fake_view", False):
            return AuditLog.objects.none()

        user = self.request.user
        qs = AuditLog.objects.select_related('user').order_by('-created_at')
        is_admin = (
            getattr(user, 'is_staff', False)
            or getattr(user, 'is_superuser', False)
            or getattr(user, 'has_role', lambda *_: False)(Roles.ADMIN)
        )
        return qs if is_admin else qs.filter(user=user)

    def get_serializer_class(self):
        return AuditLogDetailSerializer if self.action == 'retrieve' else AuditLogListSerializer
