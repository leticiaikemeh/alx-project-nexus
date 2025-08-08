from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from .models import User, Role, UserRole
from .constants import Roles



class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name']


class UserRoleSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    role = RoleSerializer()

    class Meta:
        model = UserRole
        fields = ['id', 'user', 'role']


class UserSerializer(serializers.ModelSerializer):
    roles = RoleSerializer(many=True, read_only=True)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'roles', 'password']
        read_only_fields = ['id']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance
    
class UserMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email']


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        roles = [role.name for role in user.roles.all()]

        data.update({
            "user_id": user.id,
            "email": user.email,
            "username": user.username,
            "roles": roles,
        })
        return data

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_confirmation = serializers.CharField(write_only=True)
    role_type = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'password_confirmation', 'role_type']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirmation']:
            raise serializers.ValidationError("Passwords do not match.")
        validate_password(attrs['password'])  # enforce Django password rules
        return attrs

    def create(self, validated_data):
        role_type = validated_data.pop('role_type', None)
        validated_data.pop('password_confirmation')

        # Apply role fallback logic here
        if not role_type or role_type != Roles.CUSTOMER:
            # Allow only staff to assign privileged roles
            request = self.context.get("request")
            if not request or not request.user.is_authenticated or not request.user.has_role(Roles.ADMIN):
                role_type = Roles.CUSTOMER  # Fallback to 'customer' if not allowed

        user = User.objects.create_user(**validated_data)
        user._pending_role = role_type.lower()  # Signal picks this up
        return user
        