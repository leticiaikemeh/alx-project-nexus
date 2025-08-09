from rest_framework import viewsets, generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response

from .models import User, Role, UserRole
from .constants import Roles
from .serializers import (
    UserSerializer,
    RoleSerializer,
    UserRoleSerializer,
    CustomTokenObtainPairSerializer,
    UserRegistrationSerializer
)
from .permissions import IsAdminRole, IsSelfOrAdmin, RolePermission
from apps.core.pagination import (
    SmallResultsSetPagination,
    MediumResultsSetPagination
)


class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated, RolePermission([Roles.ADMIN])]


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    pagination_class = MediumResultsSetPagination


    def get_permissions(self):
        if self.action in ['list', 'create', 'destroy']:
            return [IsAuthenticated(), RolePermission([Roles.ADMIN])()]
        elif self.action in ['retrieve', 'update', 'partial_update']:
            return [IsAuthenticated(), IsSelfOrAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        # Optimize role preloading
        return User.objects.prefetch_related(
            'roles',
            'user_roles__role'
        ).only('id', 'email', 'username', 'is_active', 'is_staff')


class UserRoleViewSet(viewsets.ModelViewSet):
    queryset = UserRole.objects.select_related('user', 'role')
    serializer_class = UserRoleSerializer
    permission_classes = [IsAuthenticated, RolePermission([Roles.ADMIN])]


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        return Response({
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username,
            },
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_201_CREATED)


class VendorListView(generics.ListAPIView):
    queryset = User.objects.vendors().only('id', 'email', 'username')
    serializer_class = UserSerializer
    permission_classes = [IsAdminRole]
