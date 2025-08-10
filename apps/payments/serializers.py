from decimal import Decimal
from django.db import models, transaction
from rest_framework import serializers
from .models import Payment, Refund
from apps.authentication.serializers import UserMinimalSerializer


# ---------- READ SERIALIZERS ----------

class RefundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Refund
        fields = ['id', 'payment', 'amount', 'status', 'created_at']
        read_only_fields = fields


class PaymentSerializer(serializers.ModelSerializer):
    user = UserMinimalSerializer(read_only=True)
    refunds = RefundSerializer(many=True, read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'user', 'amount', 'status', 'payment_method',
            'transaction_id', 'created_at', 'updated_at', 'refunds'
        ]
        read_only_fields = fields


# ---------- WRITE SERIALIZERS (with validation) ----------

class RefundCreateSerializer(serializers.ModelSerializer):
    # Accept payment as ID; we do object-level checks below.
    payment = serializers.PrimaryKeyRelatedField(queryset=Payment.objects.all())

    class Meta:
        model = Refund
        fields = ['payment', 'amount']  # status/created_at are system-managed

    def validate_amount(self, value: Decimal) -> Decimal:
        if value is None or value <= 0:
            raise serializers.ValidationError("Refund amount must be greater than zero.")
        return value

    def validate(self, attrs):
        """
        Cross-field and business-rule validation:
        - User must own the payment unless admin/staff.
        - Payment must be in 'success' state.
        - Total refunded + new amount must not exceed payment.amount.
        """
        request = self.context.get('request')
        if request is None or not request.user.is_authenticated:
            # Should be blocked at permission layer, but keep a guard.
            raise serializers.ValidationError("Authentication required.")

        payment: Payment = attrs['payment']
        amount: Decimal = attrs['amount']

        # Ownership/admin check
        is_admin = getattr(request.user, 'is_staff', False) or getattr(request.user, 'is_superuser', False)
        if not is_admin and payment.user_id != request.user.id:
            raise serializers.ValidationError("You cannot refund a payment that is not yours.")

        # Payment status check
        if payment.status != Payment.STATUS_SUCCESS:
            raise serializers.ValidationError("Only successful payments can be refunded.")

        # Over-refund protection
        already_refunded = (
            Refund.objects
            .filter(payment_id=payment.id)
            .aggregate(total=models.Sum('amount'))
            .get('total') or Decimal('0')
        )
        remaining = (payment.amount or Decimal('0')) - already_refunded
        if amount > remaining:
            raise serializers.ValidationError(
                f"Refund amount exceeds remaining refundable balance ({remaining})."
            )

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        """
        Keep creation atomic. Optionally set a default status here
        (e.g., 'pending' until a PSP confirms).
        """
        refund = Refund.objects.create(
            **validated_data,
            status='pending'  # or 'approved' if business rules say so
        )
        return refund
