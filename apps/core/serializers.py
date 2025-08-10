from rest_framework import serializers
from .models import Address, AuditLog
from apps.authentication.serializers import UserMinimalSerializer

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'street', 'city', 'state', 'country', 'zip_code', 'is_default_shipping']
        read_only_fields = ['id']

class AuditLogListSerializer(serializers.ModelSerializer):
    user = UserMinimalSerializer(read_only=True)
    class Meta:
        model = AuditLog
        fields = ['id', 'user', 'action', 'created_at']

class AuditLogDetailSerializer(serializers.ModelSerializer):
    user = UserMinimalSerializer(read_only=True)
    class Meta:
        model = AuditLog
        fields = ['id', 'user', 'action', 'created_at', 'details']
