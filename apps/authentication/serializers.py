# apps/authentication/serializers.py
from typing import Any, Dict, List
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User, Role, UserRole
from .constants import Roles


class RoleSerializer(serializers.ModelSerializer):
    """
    Serializer for the Role model.

    Fields:
        id (int): Primary key.
        name (str): Role name (e.g., 'admin', 'staff', 'customer').
    """

    class Meta:
        model = Role
        fields = ["id", "name"]


class UserRoleSerializer(serializers.ModelSerializer):
    """
    Serializer for the UserRole mapping model.

    Fields:
        id (int): Primary key of the mapping row.
        user (int): Foreign key to User (primary key value).
        role (Role): Nested role object.
    """

    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    role = RoleSerializer()

    class Meta:
        model = UserRole
        fields = ["id", "user", "role"]


class UserSerializer(serializers.ModelSerializer):
    """
    Full user serializer for create/retrieve/update operations.

    Notes:
        - `password` is write-only and validated via Django's password hashers on save.
        - `roles` is read-only (derived from the related roles for the user).
        - `id` is read-only.

    Create:
        Expects: email, username, first_name, last_name, password
        Behavior: sets hashed password before saving.

    Update:
        Optional: password. If provided, it is re-hashed and saved.

    Security:
        Do NOT echo plaintext passwords in logs or responses.
    """

    roles = RoleSerializer(many=True, read_only=True)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "roles",
            "password",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data: Dict[str, Any]) -> User:
        """
        Create a new user with a properly hashed password.

        Args:
            validated_data: Incoming validated fields.

        Returns:
            User: Newly created user instance.
        """
        password = validated_data.pop("password")
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance: User, validated_data: Dict[str, Any]) -> User:
        """
        Update an existing user and optionally rotate the password.

        Args:
            instance: Existing user instance.
            validated_data: Fields to be updated; may include 'password'.

        Returns:
            User: Updated user instance.
        """
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class UserMinimalSerializer(serializers.ModelSerializer):
    """
    Minimal user projection for lightweight references.

    Fields:
        id (int)
        email (str)
    """

    class Meta:
        model = User
        fields = ["id", "email"]


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    JWT token obtain serializer that augments the default payload.

    Extends:
        - `access` (str): JWT access token.
        - `refresh` (str): JWT refresh token.
        - `user_id` (int)
        - `email` (str)
        - `username` (str)
        - `roles` (List[str])

    Usage:
        Bind to your login view so clients receive role info alongside tokens.
    """

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        data = super().validate(attrs)
        user: User = self.user
        roles: List[str] = [role.name for role in user.roles.all()]
        data.update(
            {
                "user_id": user.id,
                "email": user.email,
                "username": user.username,
                "roles": roles,
            }
        )
        return data


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Self-service registration serializer with role safeguards.

    Fields (write-only where applicable):
        email (str)
        username (str)
        password (str, write-only)
        password_confirmation (str, write-only)
        role_type (str, write-only, optional):
            Intended role name. Only staff/Admin may assign privileged roles.
            Non-privileged registrations fall back to `Roles.CUSTOMER`.

    Validation:
        - Ensures password == password_confirmation.
        - Applies Django's `validate_password` policy.

    Create:
        - Creates the user via `create_user` (ensuring proper hashing).
        - Sets `_pending_role` (lowercased) for assignment via a signal/handler.

    Security:
        - Never return password fields in responses.
        - Enforce server-side checks even if client omits `role_type`.
    """

    password = serializers.CharField(write_only=True)
    password_confirmation = serializers.CharField(write_only=True)
    role_type = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            "email",
            "username",
            "password",
            "password_confirmation",
            "role_type",
        ]

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        if attrs["password"] != attrs["password_confirmation"]:
            raise serializers.ValidationError("Passwords do not match.")
        # Enforce Django's configured password validators
        validate_password(attrs["password"])
        return attrs

    def create(self, validated_data: Dict[str, Any]) -> User:
        role_type = validated_data.pop("role_type", None)
        validated_data.pop("password_confirmation")

        # Role fallback & authorization guard:
        # Only authenticated staff/Admin may assign privileged roles.
        if not role_type or role_type != Roles.CUSTOMER:
            request = self.context.get("request")
            if (
                not request
                or not request.user.is_authenticated
                or not request.user.has_role(Roles.ADMIN)
            ):
                role_type = Roles.CUSTOMER

        user = User.objects.create_user(**validated_data)
        # Downstream signal/handler should read this and attach the correct Role
        user._pending_role = role_type.lower()
        return user
