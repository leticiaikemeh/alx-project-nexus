from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PaymentViewSet,
    RefundViewSet
)

router = DefaultRouter()
router.register(r'Payment', PaymentViewSet, basename='payment')
router.register(r'refunf', RefundViewSet, basename='refund')

urlpatterns = [
    path('', include(router.urls)),
]
