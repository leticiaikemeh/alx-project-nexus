# apps/payments/views.py
from __future__ import annotations

from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiResponse,
    OpenApiParameter,
)
from .models import Payment, Refund
from .serializers import PaymentSerializer, RefundSerializer, RefundCreateSerializer
from apps.authentication.constants import Roles
from apps.authentication.permissions import (
    IsOwnerOrAdmin,
    IsRefundOwnerOrAdminForCreate,
)


@extend_schema_view(
    list=extend_schema(
        summary="List payments",
        description=(
            "Return payments visible to the caller.\n\n"
            "- **Users** see only their own payments.\n"
            "- **Admins** (is_staff/superuser/role=ADMIN) see all payments."
        ),
        tags=["Payments"],
        responses={200: OpenApiResponse(
            response=PaymentSerializer(many=True))},
    ),
    retrieve=extend_schema(
        summary="Retrieve a payment",
        description="Get a single payment by ID.",
        tags=["Payments"],
        responses={
            200: OpenApiResponse(response=PaymentSerializer),
            404: OpenApiResponse(description="Not found"),
        },
    ),
    # Exclude write endpoints if payments are read-only in your system.
    # Remove these excludes if you actually support payment creates/updates/deletes.
    create=extend_schema(exclude=True),
    update=extend_schema(exclude=True),
    partial_update=extend_schema(exclude=True),
    destroy=extend_schema(exclude=True),
)
class PaymentViewSet(viewsets.ModelViewSet):
    """
    Payment API.

    Access model:
    - Regular users: can list/retrieve only their own payments.
    - Admins (is_staff/superuser/role=ADMIN): can access all payments.

    Notes
    -----
    This viewset is declared as `ModelViewSet`, but write actions are typically
    disabled for payments (managed by PSP/webhooks). We exclude them from the
    OpenAPI schema to avoid misleading docs. If you do support manual create/
    update/delete, remove the `exclude=True` decorators above and provide a
    write-capable serializer.
    """

    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    queryset = Payment.objects.none()

    def get_queryset(self):
        # NEW
        if getattr(self, "swagger_fake_view", False):
            return Payment.objects.none()

        user = self.request.user
        qs = Payment.objects.select_related("user").prefetch_related("refunds")
        is_admin = getattr(user, "is_staff", False) or getattr(
            user, "has_role", lambda *_: False)(Roles.ADMIN)
        return qs if is_admin else qs.filter(user=user)


@extend_schema_view(
    list=extend_schema(
        summary="List refunds",
        description=(
            "Return refunds visible to the caller.\n\n"
            "- **Users** see only refunds for their own payments.\n"
            "- **Admins** (is_staff/superuser/role=ADMIN) see all refunds."
        ),
        tags=["Refunds"],
        responses={200: OpenApiResponse(response=RefundSerializer(many=True))},
    ),
    retrieve=extend_schema(
        summary="Retrieve a refund",
        tags=["Refunds"],
        responses={
            200: OpenApiResponse(response=RefundSerializer),
            404: OpenApiResponse(description="Not found"),
        },
    ),
    create=extend_schema(
        summary="Create a refund",
        description=(
            "Create a refund for a **successful** payment.\n\n"
            "Business rules enforced:\n"
            "1) Caller must be authenticated.\n"
            "2) Non-admins can only refund their own payments.\n"
            "3) Payment must be in `success` state.\n"
            "4) Prevents over-refund beyond original amount."
        ),
        tags=["Refunds"],
        request=RefundCreateSerializer,
        responses={
            201: OpenApiResponse(response=RefundSerializer, description="Refund created"),
            400: OpenApiResponse(description="Validation error"),
            401: OpenApiResponse(description="Authentication required"),
            403: OpenApiResponse(description="Forbidden"),
        },
        parameters=[
            # Optional: If you implement idempotency, document a header like this:
            # OpenApiParameter(
            #     name="Idempotency-Key",
            #     required=False,
            #     type=str,
            #     location=OpenApiParameter.HEADER,
            #     description="Provide to safely retry refund creations."
            # )
        ],
    ),
    # refunds usually not updatable
    update=extend_schema(exclude=True),
    # refunds usually not partially updatable
    partial_update=extend_schema(exclude=True),
    # refunds usually not deletable
    destroy=extend_schema(exclude=True),
)
class RefundViewSet(viewsets.ModelViewSet):
    """
    Refund API.

    Create path enforces the payment status and ownership rules in the serializer.
    List/Retrieve follow ownership rules similar to payments. Update/Delete are
    excluded by default (typical fintech policy).
    """

    permission_classes = [IsRefundOwnerOrAdminForCreate]

    queryset = Refund.objects.none()

    def get_queryset(self):
        # NEW
        if getattr(self, "swagger_fake_view", False):
            return Refund.objects.none()

        user = self.request.user
        qs = Refund.objects.select_related("payment", "payment__user")
        is_admin = (
            getattr(user, "is_staff", False)
            or getattr(user, "is_superuser", False)
            or getattr(user, "has_role", lambda *_: False)(Roles.ADMIN)
        )
        return qs if is_admin else qs.filter(payment__user=user)

    def get_serializer_class(self):  # type: ignore
        return RefundCreateSerializer if self.action == "create" else RefundSerializer

    def perform_create(self, serializer):
        """
        Persist refund atomically; business rules live in the serializer.
        """
        serializer.save()
