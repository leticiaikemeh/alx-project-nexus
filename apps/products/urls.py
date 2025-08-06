from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet,
    ProductViewSet,
    ProductVariantViewSet,
    ProductMediaViewSet,
    ProductReviewViewSet
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'products', ProductViewSet)
router.register(r'variants', ProductVariantViewSet)
router.register(r'media', ProductMediaViewSet)
router.register(r'reviews', ProductReviewViewSet)

urlpatterns = router.urls
