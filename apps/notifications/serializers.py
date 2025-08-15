# apps/notifications/serializers.py
from __future__ import annotations

from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample
from .models import Notification
from apps.authentication.serializers import UserMinimalSerializer

NOTIFICATION_EXAMPLE = OpenApiExample(
    name="Notification",
    summary="Example notification payload",
    value={
        "id": 123,
        "user": {"id": "9c1c2d3e-1111-2222-3333-444455556666", "email": "user@example.com"},
        "type": "order_update",
        "message": "Your order ORD-2025-000123 has shipped.",
        "is_read": False,
        "created_at": "2025-08-13T11:45:12Z",
    },
)


@extend_schema_serializer(component_name="Notification", examples=[NOTIFICATION_EXAMPLE])
class NotificationSerializer(serializers.ModelSerializer):
    """
    Read-only representation of a user notification.

    Fields
    ------
    - user: denormalized minimal user info (read-only)
    - is_read: clients typically toggle via a dedicated endpoint, not generic update
    """
    user = UserMinimalSerializer(read_only=True)

    class Meta:
        model = Notification
        fields = ["id", "user", "type", "message", "is_read", "created_at"]
        read_only_fields = ["id", "user", "created_at"]
