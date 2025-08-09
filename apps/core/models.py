from django.db import models
from django.db.models import Q
from apps.authentication.models import User


class AddressQuerySet(models.QuerySet):
    def for_user(self, user):
        return self.filter(user=user)

    def default_shipping(self):
        return self.filter(is_default_shipping=True)

    def city(self, city_name: str):
        return self.filter(city__iexact=city_name.strip())

    def country(self, country_name: str):
        return self.filter(country__iexact=country_name.strip())


class Address(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='addresses', db_index=True
    )
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=100, db_index=True)
    state = models.CharField(max_length=100, db_index=True)
    country = models.CharField(max_length=100, db_index=True)
    zip_code = models.CharField(max_length=20, db_index=True)
    is_default_shipping = models.BooleanField(default=False, db_index=True)

    objects = AddressQuerySet.as_manager()

    class Meta:
        ordering = ['user_id', 'country', 'state', 'city', 'street']
        indexes = [
            models.Index(fields=['user']),                      # frequent join/filter
            models.Index(fields=['user', 'is_default_shipping']),
            models.Index(fields=['country', 'state', 'city']),
            models.Index(fields=['zip_code']),
        ]
        constraints = [
            # At most one default shipping address per user
            models.UniqueConstraint(
                fields=['user'],
                condition=Q(is_default_shipping=True),
                name='uniq_user_default_shipping'
            ),
        ]

    def __str__(self):
        return f'{self.street}, {self.city}, {self.state}, {self.country} ({self.zip_code})'

class AuditLogQuerySet(models.QuerySet):
    def for_user(self, user):
        return self.filter(user=user)

    def action(self, action: str):
        return self.filter(action__iexact=action)

    def recent(self):
        return self.order_by('-created_at')

    def since(self, dt):
        return self.filter(created_at__gte=dt)


class AuditLog(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='audit_logs', db_index=True
    )
    action = models.CharField(max_length=255, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    # JSONField from django.db.models (Postgres to jsonb)
    details = models.JSONField(default=dict, blank=True)

    objects = AuditLogQuerySet.as_manager()

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['action', 'created_at']),
        ]
      
    def __str__(self):
        return f'{self.user.email} - {self.action} @ {self.created_at:%Y-%m-%d %H:%M:%S}'
