from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Payment, Refund
from .serializers import PaymentSerializer, RefundSerializer, RefundCreateSerializer
from apps.authentication.constants import Roles
from apps.authentication.permissions import (
    IsOwnerOrAdmin,
    IsRefundOwnerOrAdminForCreate
)


class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        user = self.request.user
        qs = Payment.objects.select_related('user').prefetch_related('refunds')

        if user.is_staff or user.has_role(Roles.ADMIN):
            return qs
        return qs.filter(user=user)

class RefundViewSet(viewsets.ModelViewSet):
    permission_classes = [IsRefundOwnerOrAdminForCreate]

    def get_queryset(self):
        user = self.request.user
        qs = Refund.objects.select_related('payment', 'payment__user')
        return qs if (user.is_staff or getattr(user, 'is_superuser', False) or user.has_role(Roles.ADMIN)) else qs.filter(payment__user=user)

    def get_serializer_class(self):
        return RefundCreateSerializer if self.action == 'create' else RefundSerializer

    def perform_create(self, serializer):
        serializer.save()  # all business rules in serializer.validate()

