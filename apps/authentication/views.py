from typing import Any, Dict, List

from rest_framework import viewsets, generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiResponse,
    OpenApiExample,
)

from .models import User, Role, UserRole
from .constants import Roles
from .serializers import (
    UserSerializer,
    RoleSerializer,
    UserRoleSerializer,
    CustomTokenObtainPairSerializer,
    UserRegistrationSerializer,
)
from .permissions import IsAdminRole, IsSelfOrAdmin, RolePermission
from apps.core.pagination import (
    SmallResultsSetPagination,
    MediumResultsSetPagination,
)


# ---------- RoleViewSet ----------

@extend_schema_view(
    list=extend_schema(
        summary="List roles",
        description="Returns all available roles.",
        tags=["Auth: Roles"],
        responses={200: RoleSerializer(many=True)},
        security=[{"bearerAuth": []}],
    ),
    retrieve=extend_schema(
        summary="Get a role",
        tags=["Auth: Roles"],
        responses={200: RoleSerializer},
        security=[{"bearerAuth": []}],
    ),
    create=extend_schema(
        summary="Create role",
        tags=["Auth: Roles"],
        request=RoleSerializer,
        responses={201: RoleSerializer},
        security=[{"bearerAuth": []}],
    ),
    update=extend_schema(
        summary="Replace role",
        tags=["Auth: Roles"],
        request=RoleSerializer,
        responses={200: RoleSerializer},
        security=[{"bearerAuth": []}],
    ),
    partial_update=extend_schema(
        summary="Update role (partial)",
        tags=["Auth: Roles"],
        request=RoleSerializer,
        responses={200: RoleSerializer},
        security=[{"bearerAuth": []}],
    ),
    destroy=extend_schema(
        summary="Delete role",
        tags=["Auth: Roles"],
        responses={204: OpenApiResponse(description="Role deleted")},
        security=[{"bearerAuth": []}],
    ),
)
class RoleViewSet(viewsets.ModelViewSet):
    """
    Manage system roles (admin-only).

    Permissions:
        - Authenticated + Admin role required for all actions.

    Returns:
        Standard CRUD for Role model.
    """
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated, RolePermission([Roles.ADMIN])]


# ---------- UserViewSet ----------

@extend_schema_view(
    list=extend_schema(
        summary="List users",
        description=(
            "Paginated list of users. Admin-only.\n\n"
            "Pagination: `page` (1-based), `page_size` (<= 50)."
        ),
        tags=["Auth: Users"],
        parameters=[
            OpenApiParameter(name="page", location=OpenApiParameter.QUERY, required=False, type=int,
                             description="1-based page index."),
            OpenApiParameter(name="page_size", location=OpenApiParameter.QUERY, required=False, type=int,
                             description="Items per page (max 50)."),
        ],
        responses={200: UserSerializer(many=True)},
        security=[{"bearerAuth": []}],
    ),
    retrieve=extend_schema(
        summary="Get a user",
        description="Retrieve a user. Allowed for self or admin.",
        tags=["Auth: Users"],
        responses={200: UserSerializer},
        security=[{"bearerAuth": []}],
    ),
    create=extend_schema(
        summary="Create user",
        description="Admin-only user creation.",
        tags=["Auth: Users"],
        request=UserSerializer,
        responses={201: UserSerializer},
        security=[{"bearerAuth": []}],
    ),
    update=extend_schema(
        summary="Replace user",
        description="Update all fields. Allowed for self or admin.",
        tags=["Auth: Users"],
        request=UserSerializer,
        responses={200: UserSerializer},
        security=[{"bearerAuth": []}],
    ),
    partial_update=extend_schema(
        summary="Update user (partial)",
        description="Partial update. Allowed for self or admin.",
        tags=["Auth: Users"],
        request=UserSerializer,
        responses={200: UserSerializer},
        security=[{"bearerAuth": []}],
    ),
    destroy=extend_schema(
        summary="Delete user",
        description="Admin-only.",
        tags=["Auth: Users"],
        responses={204: OpenApiResponse(description="User deleted")},
        security=[{"bearerAuth": []}],
    ),
)
class UserViewSet(viewsets.ModelViewSet):
    """
    Manage users with fine-grained permissions.

    Permissions:
        - list/create/destroy: Admin only.
        - retrieve/update/partial_update: Self or admin.

    Pagination:
        MediumResultsSetPagination (page/page_size up to 50).

    Optimization:
        Prefetch roles and limit selected fields for performance.
    """
    serializer_class = UserSerializer
    pagination_class = MediumResultsSetPagination

    def get_permissions(self):
        if self.action in ["list", "create", "destroy"]:
            return [IsAuthenticated(), RolePermission([Roles.ADMIN])()]
        elif self.action in ["retrieve", "update", "partial_update"]:
            return [IsAuthenticated(), IsSelfOrAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        # Optimize role preloading
        return (
            User.objects.prefetch_related("roles", "user_roles__role")
            .only("id", "email", "username", "is_active", "is_staff")
        )


# ---------- UserRoleViewSet ----------

@extend_schema_view(
    list=extend_schema(
        summary="List user-role assignments",
        tags=["Auth: UserRoles"],
        responses={200: UserRoleSerializer(many=True)},
        security=[{"bearerAuth": []}],
    ),
    retrieve=extend_schema(
        summary="Get a user-role assignment",
        tags=["Auth: UserRoles"],
        responses={200: UserRoleSerializer},
        security=[{"bearerAuth": []}],
    ),
    create=extend_schema(
        summary="Assign role to user",
        tags=["Auth: UserRoles"],
        request=UserRoleSerializer,
        responses={201: UserRoleSerializer},
        security=[{"bearerAuth": []}],
    ),
    update=extend_schema(
        summary="Replace user-role assignment",
        tags=["Auth: UserRoles"],
        request=UserRoleSerializer,
        responses={200: UserRoleSerializer},
        security=[{"bearerAuth": []}],
    ),
    partial_update=extend_schema(
        summary="Update user-role assignment (partial)",
        tags=["Auth: UserRoles"],
        request=UserRoleSerializer,
        responses={200: UserRoleSerializer},
        security=[{"bearerAuth": []}],
    ),
    destroy=extend_schema(
        summary="Delete user-role assignment",
        tags=["Auth: UserRoles"],
        responses={204: OpenApiResponse(description="Assignment deleted")},
        security=[{"bearerAuth": []}],
    ),
)
class UserRoleViewSet(viewsets.ModelViewSet):
    """
    Manage assignments between users and roles (admin-only).
    """
    queryset = UserRole.objects.select_related("user", "role")
    serializer_class = UserRoleSerializer
    permission_classes = [IsAuthenticated, RolePermission([Roles.ADMIN])]


# ---------- JWT: login ----------

class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Obtain JWT access/refresh tokens, augmented with user profile & roles.

    Request:
        email (str), password (str)

    Response:
        access (str), refresh (str), user_id (int), email (str),
        username (str), roles (list[str])
    """
    serializer_class = CustomTokenObtainPairSerializer

    @extend_schema(
        summary="Login (JWT obtain)",
        tags=["Auth: JWT"],
        request={"$ref": "#/components/schemas/TokenObtainRequest"},
        responses={200: {"$ref": "#/components/schemas/TokenObtainResponse"}},
        # This endpoint itself is public; tokens protect subsequent calls.
        security=[],
        examples=[
            OpenApiExample(
                "Login example",
                value={"email": "user@example.com", "password": "P@ssw0rd!"},
                request_only=True,
            )
        ],
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


# ---------- Registration (public) ----------

class UserRegistrationView(generics.CreateAPIView):
    """
    Public user registration with safe role fallback.

    - If `role_type` is not allowed, it falls back to 'customer'.
    - Returns created user + JWT tokens for immediate auth.
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Register",
        tags=["Auth: Registration"],
        request={"$ref": "#/components/schemas/UserRegistrationRequest"},
        responses={201: {"$ref": "#/components/schemas/TokenObtainResponse"}},
        security=[],
        examples=[
            OpenApiExample(
                "Register example",
                value={
                    "email": "newuser@example.com",
                    "username": "newuser",
                    "password": "P@ssw0rd!",
                    "password_confirmation": "P@ssw0rd!",
                    "role_type": "customer",
                },
                request_only=True,
            )
        ],
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user: User = serializer.save()

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                },
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )


# ---------- Vendor list (admin-only) ----------

class VendorListView(generics.ListAPIView):
    """
    List all users who are vendors. Admin-only.

    Pagination:
        Uses SmallResultsSetPagination by default unless overridden.
    """
    queryset = User.objects.vendors().only("id", "email", "username")
    serializer_class = UserSerializer
    permission_classes = [IsAdminRole]
    pagination_class = SmallResultsSetPagination

    @extend_schema(
        summary="List vendors",
        description="Returns a small, paginated list of vendor users (admin-only).",
        tags=["Auth: Users"],
        parameters=[
            OpenApiParameter(
                name="page", location=OpenApiParameter.QUERY, required=False, type=int),
            OpenApiParameter(name="page_size", location=OpenApiParameter.QUERY, required=False, type=int,
                             description="Items per page (max 10)."),
        ],
        responses={200: UserSerializer(many=True)},
        security=[{"bearerAuth": []}],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
