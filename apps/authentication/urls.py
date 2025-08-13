# apps/authentication/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    UserViewSet,
    RoleViewSet,
    UserRoleViewSet,
    CustomTokenObtainPairView,
    UserRegistrationView,
    VendorListView,
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='users')
router.register(r'roles', RoleViewSet, basename='roles')
router.register(r'user-roles', UserRoleViewSet, basename='user-roles')

# Expose two lists so project urls can mount them under different prefixes
resource_urlpatterns = [
    # /users/, /roles/, /user-roles/
    path('', include(router.urls)),
    path('vendors/', VendorListView.as_view(), name='vendor-list'),
]

auth_urlpatterns = [
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', UserRegistrationView.as_view(), name='user-register'),
]
