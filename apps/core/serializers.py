# apps/core/serializers.py
from __future__ import annotations

from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample
from .models import Address, AuditLog
from apps.authentication.serializers import UserMinimalSerializer

# ---------- OpenAPI Examples ----------

ADDRESS_EXAMPLE = OpenApiExample(
    name="Address",
    summary="Example shipping address",
    value={
        "id": 101,
        "street": "12 Admiralty Way",
        "city": "Lekki",
        "state": "Lagos",
        "country": "NG",
        "zip_code": "105102",
        "is_default_shipping": True,
    },
)

AUDIT_LOG_LIST_EXAMPLE = OpenApiExample(
    name="AuditLogList",
    summary="Audit entry (list view)",
    value={
        "id": 555,
        "user": {"id": "1a2b3c4d-0000-1111-2222-333344445555", "email": "ops@example.com"},
        "action": "ORDER_STATUS_UPDATED",
        "created_at": "2025-08-13T11:20:01Z",
    },
)

AUDIT_LOG_DETAIL_EXAMPLE = OpenApiExample(
    name="AuditLogDetail",
    summary="Audit entry (detail view)",
    value={
        "id": 555,
        "user": {"id": "1a2b3c4d-0000-1111-2222-333344445555", "email": "ops@example.com"},
        "action": "ORDER_STATUS_UPDATED",
        "created_at": "2025-08-13T11:20:01Z",
        "details": {
            "order_id": 42,
            "from": "pending",
            "to": "shipped",
            "reason": "Warehouse dispatch",
        },
    },
)

# ---------- Serializers ----------


@extend_schema_serializer(component_name="Address", examples=[ADDRESS_EXAMPLE])
class AddressSerializer(serializers.ModelSerializer):
    """
    Shipping/billing address.

    Notes
    -----
    - `is_default_shipping` can be used by clients to mark preferred shipping address.
    - If you enforce one default per user, do that in the view/serializer logic.
    """
    class Meta:
        model = Address
        fields = ['id', 'street', 'city', 'state',
                  'country', 'zip_code', 'is_default_shipping']
        read_only_fields = ['id']


@extend_schema_serializer(component_name="AuditLogList", examples=[AUDIT_LOG_LIST_EXAMPLE])
class AuditLogListSerializer(serializers.ModelSerializer):
    """
    Lightweight audit log representation for list endpoints.
    """
    user = UserMinimalSerializer(read_only=True)

    class Meta:
        model = AuditLog
        fields = ['id', 'user', 'action', 'created_at']


@extend_schema_serializer(component_name="AuditLogDetail", examples=[AUDIT_LOG_DETAIL_EXAMPLE])
class AuditLogDetailSerializer(serializers.ModelSerializer):
    """
    Detailed audit log representation including structured `details`.
    """
    user = UserMinimalSerializer(read_only=True)

    class Meta:
        model = AuditLog
        fields = ['id', 'user', 'action', 'created_at', 'details']
