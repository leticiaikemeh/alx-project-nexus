from rest_framework import viewsets, permissions,filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import (
    Category,
    Product,
    ProductVariant,
    ProductMedia,
    ProductReview
)
from .serializers import (
    CategorySerializer,
    ProductSerializer,
    ProductVariantSerializer,
    ProductMediaSerializer,
    ProductReviewSerializer
)
from apps.authentication.permissions import RolePermission


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated, RolePermission(['admin', 'staff'])]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.prefetch_related('variants', 'media', 'reviews').all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    # Search by name or description
    search_fields = ['name', 'description']

    # Filter by category and price
    filterset_fields = {
        'category': ['exact'],
        'price': ['gte', 'lte'],
        'is_active': ['exact']
    }

    # Allow ordering by price, name, or creation date
    ordering_fields = ['price', 'name', 'created_at']
    ordering = ['-created_at']  # default ordering

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), RolePermission(['admin', 'staff'])()]
        return [permissions.AllowAny()]


class ProductVariantViewSet(viewsets.ModelViewSet):
    queryset = ProductVariant.objects.select_related('product').all()
    serializer_class = ProductVariantSerializer
    permission_classes = [permissions.IsAuthenticated, RolePermission(['admin', 'staff'])]


class ProductMediaViewSet(viewsets.ModelViewSet):
    queryset = ProductMedia.objects.select_related('product').all()
    serializer_class = ProductMediaSerializer
    permission_classes = [permissions.IsAuthenticated, RolePermission(['admin', 'staff'])]


class ProductReviewViewSet(viewsets.ModelViewSet):
    queryset = ProductReview.objects.select_related('user', 'product').all()
    serializer_class = ProductReviewSerializer

    def perform_create(self, serializer):
        # Attach the authenticated user to the review
        serializer.save(user=self.request.user)

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            # Users can only modify their own reviews
            return [permissions.IsAuthenticated()]
        elif self.action == 'create':
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]
