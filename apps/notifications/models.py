from django.db import models
from apps.authentication.models import User


class NotificationQuerySet(models.QuerySet):
    def for_user(self, user):
        return self.filter(user=user)

    def unread(self):
        return self.filter(is_read=False)

    def recent(self):
        return self.order_by('-created_at')


class Notification(models.Model):
    class Type(models.TextChoices):
        INFO = 'info', 'Info'
        WARNING = 'warning', 'Warning'
        SUCCESS = 'success', 'Success'
        ERROR = 'error', 'Error'

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        db_index=True,  # explicit for clarity
    )
    type = models.CharField(
        max_length=20,
        choices=Type.choices,
        db_index=True,
    )
    message = models.TextField()
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    objects = NotificationQuerySet.as_manager()

    class Meta:
        ordering = ['-created_at']
        indexes = [
            # Common filters/sorts:
            models.Index(fields=['user']),
            models.Index(fields=['is_read']),
            models.Index(fields=['type']),
            models.Index(fields=['created_at']),
            # Fast path for inbox view: unread for a user by recency
            models.Index(fields=['user', 'is_read', '-created_at']),
        ]

    def __str__(self):
        return f'{self.get_type_display()} → {self.user.email} ({"" if self.is_read else "un"}read)'
