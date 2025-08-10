from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AddressViewSet, AuditLogViewSet

router = DefaultRouter()
router.register('addresses', AddressViewSet, basename='address')
router.register('audit-logs', AuditLogViewSet, basename='audit-log')

urlpatterns = [
    path('', include(router.urls)),
]

