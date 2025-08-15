# apps/notifications/views.py
from __future__ import annotations

from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse

from .models import Notification
from .serializers import NotificationSerializer
from apps.authentication.constants import Roles


@extend_schema_view(
    list=extend_schema(
        summary="List my notifications (admins see all)",
        description=(
            "Returns notifications visible to the caller.\n\n"
            "- **Users** see only their own notifications.\n"
            "- **Admins** (is_staff/superuser/role=ADMIN) see all notifications."
        ),
        tags=["Notifications"],
        responses={200: OpenApiResponse(
            response=NotificationSerializer(many=True))},
    ),
    retrieve=extend_schema(
        summary="Retrieve a notification",
        tags=["Notifications"],
        responses={200: OpenApiResponse(
            response=NotificationSerializer), 404: OpenApiResponse(description="Not found")},
    ),
    create=extend_schema(exclude=True),
    update=extend_schema(exclude=True),
    partial_update=extend_schema(exclude=True),
    destroy=extend_schema(exclude=True),
)
class NotificationViewSet(viewsets.ModelViewSet):
    """
    Notifications API.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    # NEW
    queryset = Notification.objects.none()

    def get_queryset(self):
        # NEW
        if getattr(self, "swagger_fake_view", False):
            return Notification.objects.none()

        user = self.request.user
        qs = Notification.objects.select_related(
            "user").order_by("-created_at")
        is_admin = (
            getattr(user, "is_staff", False)
            or getattr(user, "is_superuser", False)
            or getattr(user, "has_role", lambda *_: False)(Roles.ADMIN)
        )
        return qs if is_admin else qs.filter(user=user)

    @action(detail=True, methods=["post"])
    @extend_schema(
        summary="Mark one notification as read",
        description="Marks the specified notification as read.",
        tags=["Notifications"],
        responses={200: OpenApiResponse(
            response=NotificationSerializer), 403: OpenApiResponse(description="Forbidden")},
    )
    def mark_read(self, request, pk=None):
        notif = self.get_object()
        if not (request.user == notif.user or getattr(request.user, "is_staff", False) or getattr(request.user, "has_role", lambda *_: False)(Roles.ADMIN)):
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        if not notif.is_read:
            notif.is_read = True
            notif.save(update_fields=["is_read"])
        return Response(self.get_serializer(notif).data)

    @action(detail=False, methods=["post"])
    @extend_schema(
        summary="Mark all my notifications as read",
        description="Marks all notifications belonging to the caller as read.",
        tags=["Notifications"],
        responses={200: OpenApiResponse(
            description="All notifications marked read")},
    )
    def mark_all_read(self, request):
        Notification.objects.filter(
            user=request.user, is_read=False).update(is_read=True)
        return Response({"detail": "All notifications marked read"}, status=status.HTTP_200_OK)
