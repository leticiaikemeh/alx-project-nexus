# apps/payments/serializers.py
from __future__ import annotations

from decimal import Decimal
from django.db import models, transaction
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample
from .models import Payment, Refund
from apps.authentication.serializers import UserMinimalSerializer


# ---------- OpenAPI Examples (used below) ----------

PAYMENT_EXAMPLE = OpenApiExample(
    name="Payment (successful card payment with one refund)",
    summary="Example Payment payload",
    value={
        "id": "7f6f7ab6-3e0f-4f4e-8d2b-12a123456789",
        "user": {"id": "1c2f3a44-e1cd-4c0c-bb33-9a77a778c0a1", "email": "jane@example.com"},
        "amount": "15000.00",
        "status": "success",
        "payment_method": "card",
        "transaction_id": "PSP-TXN-2025-000123",
        "created_at": "2025-08-13T10:20:30Z",
        "updated_at": "2025-08-13T10:21:05Z",
        "refunds": [
            {
                "id": "a1b2c3d4-22aa-44bb-99ff-3a3a3a3a3a3a",
                "payment": "7f6f7ab6-3e0f-4f4e-8d2b-12a123456789",
                "amount": "5000.00",
                "status": "pending",
                "created_at": "2025-08-13T10:21:05Z",
            }
        ],
    },
)

REFUND_EXAMPLE = OpenApiExample(
    name="Refund",
    summary="Example Refund payload",
    value={
        "id": "a1b2c3d4-22aa-44bb-99ff-3a3a3a3a3a3a",
        "payment": "7f6f7ab6-3e0f-4f4e-8d2b-12a123456789",
        "amount": "5000.00",
        "status": "pending",
        "created_at": "2025-08-13T10:21:05Z",
    },
)

REFUND_CREATE_EXAMPLE = OpenApiExample(
    name="RefundCreate",
    summary="Request to create a refund",
    value={"payment": "7f6f7ab6-3e0f-4f4e-8d2b-12a123456789", "amount": "5000.00"},
)


# ---------- READ SERIALIZERS ----------

@extend_schema_serializer(
    component_name="Refund",
    examples=[REFUND_EXAMPLE],
)
class RefundSerializer(serializers.ModelSerializer):
    """
    Read-only representation of a refund tied to a payment.

    Notes
    -----
    - `status` is system-managed (e.g., `pending`, `approved`, `failed`, `rejected`).
    - `payment` is the UUID of the related Payment.
    """

    class Meta:
        model = Refund
        fields = ["id", "payment", "amount", "status", "created_at"]
        read_only_fields = fields


@extend_schema_serializer(
    component_name="Payment",
    examples=[PAYMENT_EXAMPLE],
)
class PaymentSerializer(serializers.ModelSerializer):
    """
    Read-only representation of a Payment with nested minimal user info and refunds.

    Fields
    ------
    - user: denormalized minimal user (id/email) for convenience in clients
    - refunds: all refunds associated with this payment
    """

    user = UserMinimalSerializer(read_only=True)
    refunds = RefundSerializer(many=True, read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "user",
            "amount",
            "status",
            "payment_method",
            "transaction_id",
            "created_at",
            "updated_at",
            "refunds",
        ]
        read_only_fields = fields


# ---------- WRITE SERIALIZERS (with validation) ----------

@extend_schema_serializer(
    component_name="RefundCreate",
    examples=[REFUND_CREATE_EXAMPLE],
)
class RefundCreateSerializer(serializers.ModelSerializer):
    """
    Create serializer for Refunds.

    Business Rules Enforced
    -----------------------
    1) Authentication must be present.
    2) Non-admin users can only refund their own payments.
    3) Payment must be in `success` state.
    4) Prevent over-refunds: sum(existing) + requested <= payment.amount.
    """

    # Accept payment as ID; object-level checks happen in validate()
    payment = serializers.PrimaryKeyRelatedField(
        queryset=Payment.objects.all(),
        help_text="UUID of the Payment being refunded.",
    )

    class Meta:
        model = Refund
        # `status` and `created_at` are system-managed; do not expose for writes.
        fields = ["payment", "amount"]

    def validate_amount(self, value: Decimal) -> Decimal:
        """
        Ensure amount is a positive, non-zero Decimal.
        """
        if value is None or value <= 0:
            raise serializers.ValidationError(
                "Refund amount must be greater than zero.")
        return value

    def validate(self, attrs):
        """
        Cross-field and business rule checks:

        - Require authenticated user.
        - Enforce ownership unless admin/staff.
        - Only `success` payments can be refunded.
        - Prevent over-refund beyond original payment amount.
        """
        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            # Should already be blocked by permissions, but guard anyway.
            raise serializers.ValidationError("Authentication required.")

        payment: Payment = attrs["payment"]
        amount: Decimal = attrs["amount"]

        # Ownership/admin check
        is_admin = getattr(request.user, "is_staff", False) or getattr(
            request.user, "is_superuser", False)
        if not is_admin and payment.user_id != request.user.id:
            raise serializers.ValidationError(
                "You cannot refund a payment that is not yours.")

        # Payment status check
        if payment.status != Payment.STATUS_SUCCESS:
            raise serializers.ValidationError(
                "Only successful payments can be refunded.")

        # Over-refund protection
        already_refunded = (
            Refund.objects.filter(payment_id=payment.id).aggregate(
                total=models.Sum("amount")).get("total")
            or Decimal("0")
        )
        remaining = (payment.amount or Decimal("0")) - already_refunded
        if amount > remaining:
            raise serializers.ValidationError(
                f"Refund amount exceeds remaining refundable balance ({remaining})."
            )

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        """
        Create the refund atomically. If your PSP confirms asynchronously,
        consider leaving status as `pending` and updating later via webhook.
        """
        refund = Refund.objects.create(
            **validated_data,
            status="pending",  # or 'approved' if you auto-approve
        )
        return refund
