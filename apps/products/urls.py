from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet,
    ProductViewSet,
    ProductVariantViewSet,
    ProductMediaViewSet,
    ProductReviewViewSet
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename= 'categories')
router.register(r'products', ProductViewSet, basename= 'products')
router.register(r'variants', ProductVariantViewSet, basename= 'variants')
router.register(r'media', ProductMediaViewSet, basename= 'media')
router.register(r'reviews', ProductReviewViewSet, basename= 'reviews')

urlpatterns = [
    path('', include(router.urls)),
]
