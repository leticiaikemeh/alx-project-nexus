from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        if not extra_fields.get('username'):
            raise ValueError("The Username field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        if not extra_fields.get('username'):
            raise ValueError("Superuser must have a username")
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

    def with_role(self, role_name):
        return self.filter(user_roles__role__name=role_name.lower())

    def customers(self):
        return self.with_role('customer')

    def admins(self):
        return self.with_role('admin')

    def vendors(self):
        return self.with_role('vendor')

    def warehouse_staff(self):
        return self.with_role('warehouse')


class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Role"
        verbose_name_plural = "Roles"
        ordering = ["name"]


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=255, unique=True)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    roles = models.ManyToManyField(Role, through='UserRole', related_name='users')

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email or "UnnamedUser"

    def has_role(self, role_name):
        return self.user_roles.filter(role__name=role_name).exists()

    @property
    def role_list(self):
        return [ur.role for ur in self.user_roles.all()]

    def get_full_name(self):
        return f"{self.first_name or ''} {self.last_name or ''}".strip()

    class Meta:
        ordering = ['email']
        indexes = [
            models.Index(fields=['email']),
        ]


class UserRole(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_roles')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='user_roles')

    class Meta:
        unique_together = ('user', 'role')
        verbose_name = "User Role"
        verbose_name_plural = "User Roles"
        ordering = ["user"]
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['role']),
        ]

    def __str__(self):
        user_email = getattr(self.user, 'email', 'UnknownUser')
        role_name = getattr(self.role, 'name', 'UnknownRole')
        return f"{user_email} - {role_name}"
