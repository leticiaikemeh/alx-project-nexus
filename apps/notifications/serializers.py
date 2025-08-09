from rest_framework import serializers
from .models import Notification
from apps.authentication.serializers import UserMinimalSerializer

class NotificationSerializer(serializers.ModelSerializer):
    user = UserMinimalSerializer(read_only=True)

    class Meta:
        model = Notification
        fields = ['id', 'user', 'type', 'message', 'is_read', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']
