from django.db import transaction
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Address, AuditLog
from .serializers import AddressSerializer, AuditLogListSerializer, AuditLogDetailSerializer
from apps.core.pagination import SmallResultsSetPagination, MediumResultsSetPagination


class AddressViewSet(viewsets.ModelViewSet):
    """
    Users manage their own addresses.
    Optimizations:
      - owner-scoped queryset
      - select_related('user') for any reverse usage
      - small payloads via AddressSerializer
    """
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = SmallResultsSetPagination

    def get_queryset(self):
        return (
            Address.objects
            .for_user(self.request.user)
            .select_related('user')
            .only('id', 'street', 'city', 'state', 'country', 'zip_code', 'is_default_shipping', 'user_id')
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """
        Atomically set this address as the default shipping address.
        Enforced also by DB partial unique constraint.
        """
        addr = self.get_object()
        if addr.user_id != request.user.id:
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        with transaction.atomic():
            Address.objects.for_user(request.user).update(is_default_shipping=False)
            if not addr.is_default_shipping:
                addr.is_default_shipping = True
                addr.save(update_fields=['is_default_shipping'])

        return Response({'ok': True})

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Users: can only read their own logs.
    Admin/staff: can read all logs.
    Optimizations:
      - owner/admin-scoped queryset
      - select_related('user')
      - use lightweight list serializer
    """
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = MediumResultsSetPagination
    swagger_tags = ['Audit Logs']  # if you’re tagging

    def get_queryset(self):
        qs = (AuditLog.objects
              .select_related('user')
              .only('id', 'user_id', 'action', 'created_at'))
        u = self.request.user
        if u.is_staff or getattr(u, 'is_superuser', False):
            return qs
        return qs.filter(user=u)

    def get_serializer_class(self):
        return AuditLogDetailSerializer if self.action == 'retrieve' else AuditLogListSerializer
