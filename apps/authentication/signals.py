# apps/authentication/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.authentication.models import User, Role, UserRole
from .constants import Roles


@receiver(post_save, sender=User)
def assign_role_based_on_signup(sender, instance, created, **kwargs):
    if not created:
        return

    if instance.roles.exists():
        return

    # Check for temp attribute (set during registration)
    role_name = getattr(instance, '_pending_role', None)

    if not role_name:
        role_name = Roles.CUSTOMER  # fallback default

    valid_roles = [
        Roles.CUSTOMER,
        Roles.ADMIN,
        Roles.STAFF,
        Roles.WAREHOUSE,
        Roles.VENDOR
        ]
    if role_name not in valid_roles:
        role_name = 'customer'

    role, _ = Role.objects.get_or_create(name=role_name)
    UserRole.objects.create(user=instance, role=role)

    # Optional cleanup
    if hasattr(instance, '_pending_role'):
        delattr(instance, '_pending_role')
