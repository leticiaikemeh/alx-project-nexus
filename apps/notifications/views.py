from rest_framework import viewsets, permissions, mixins
from .models import Notification
from .serializers import NotificationSerializer
from apps.core.pagination import SmallResultsSetPagination

class NotificationViewSet(mixins.ListModelMixin,
                          mixins.RetrieveModelMixin,
                          mixins.UpdateModelMixin,
                          viewsets.GenericViewSet):
    """
    Typical behavior:
    - Users list/read their own notifications
    - Users can mark as read (PATCH is_read=true)
    - No create/delete from API; server creates via business logic
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = SmallResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        qs = (Notification.objects
              .for_user(user)
              .select_related('user')      # cheap and avoids extra user fetch
              .recent())                    # uses ordering & index
        # optional filter params: ?unread=1
        unread = self.request.query_params.get('unread')
        if unread in ('1', 'true', 'True'):
            qs = qs.unread()
        notif_type = self.request.query_params.get('type')
        if notif_type:
            qs = qs.filter(type=notif_type)
        return qs
