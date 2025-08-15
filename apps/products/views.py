# apps/products/views.py
from __future__ import annotations

from typing import List
from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiResponse,
)

from .models import Category, Product, ProductVariant, ProductMedia, ProductReview
from .serializers import (
    CategorySerializer,
    ProductSerializer,
    ProductVariantSerializer,
    ProductMediaSerializer,
    ProductReviewSerializer,
)
from apps.authentication.permissions import RolePermission
from apps.authentication.constants import Roles
from apps.core.pagination import SmallResultsSetPagination, MediumResultsSetPagination


# ----- Shared parameter helpers -----
_page_param_medium = OpenApiParameter(
    name="page", location=OpenApiParameter.QUERY, required=False, type=int, description="1-based page index."
)
_page_size_medium = OpenApiParameter(
    name="page_size", location=OpenApiParameter.QUERY, required=False, type=int, description="Items per page (max 50)."
)
_page_param_small = OpenApiParameter(
    name="page", location=OpenApiParameter.QUERY, required=False, type=int, description="1-based page index."
)
_page_size_small = OpenApiParameter(
    name="page_size", location=OpenApiParameter.QUERY, required=False, type=int, description="Items per page (max 10)."
)


# ========================= Categories =========================

@extend_schema_view(
    list=extend_schema(
        summary="List categories",
        tags=["Products: Categories"],
        responses={200: OpenApiResponse(
            response=CategorySerializer(many=True))},
    ),
    retrieve=extend_schema(
        summary="Get a category",
        tags=["Products: Categories"],
        responses={200: OpenApiResponse(response=CategorySerializer)},
    ),
    create=extend_schema(
        summary="Create category",
        tags=["Products: Categories"],
        request=CategorySerializer,
        responses={201: OpenApiResponse(response=CategorySerializer)},
    ),
    update=extend_schema(
        summary="Replace category",
        tags=["Products: Categories"],
        request=CategorySerializer,
        responses={200: OpenApiResponse(response=CategorySerializer)},
    ),
    partial_update=extend_schema(
        summary="Update category (partial)",
        tags=["Products: Categories"],
        request=CategorySerializer,
        responses={200: OpenApiResponse(response=CategorySerializer)},
    ),
    destroy=extend_schema(
        summary="Delete category",
        tags=["Products: Categories"],
        responses={204: OpenApiResponse(description="Category deleted")},
    ),
)
class CategoryViewSet(viewsets.ModelViewSet):
    """
    Categories catalog.

    Permissions:
      - GET/list/retrieve: public.
      - POST/PUT/PATCH/DELETE: Authenticated + privileged role required.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), RolePermission(Roles.privileged)()]


# ========================= Products =========================

@extend_schema_view(
    list=extend_schema(
        summary="List products",
        description=(
            "Paginated list of products. Supports search, filtering, and ordering.\n\n"
            "**Filters**: `category`, `price__gte`, `price__lte`, `is_active`\n"
            "**Search**: `search` across `name`, `description`\n"
            "**Ordering**: `ordering` by `price`, `name`, `created_at` (prefix with `-` for desc)"
        ),
        tags=["Products"],
        parameters=[
            _page_param_medium,
            _page_size_medium,
            OpenApiParameter(
                name="search", location=OpenApiParameter.QUERY, required=False, type=str),
            OpenApiParameter(
                name="ordering", location=OpenApiParameter.QUERY, required=False, type=str,
                description="e.g. `-created_at,price`"
            ),
            OpenApiParameter(
                name="category", location=OpenApiParameter.QUERY, required=False, type=int),
            OpenApiParameter(
                name="price__gte", location=OpenApiParameter.QUERY, required=False, type=str),
            OpenApiParameter(
                name="price__lte", location=OpenApiParameter.QUERY, required=False, type=str),
            OpenApiParameter(
                name="is_active", location=OpenApiParameter.QUERY, required=False, type=bool),
        ],
        responses={200: OpenApiResponse(
            response=ProductSerializer(many=True))},
    ),
    retrieve=extend_schema(
        summary="Get a product",
        tags=["Products"],
        responses={200: OpenApiResponse(response=ProductSerializer)},
    ),
    create=extend_schema(
        summary="Create product",
        tags=["Products"],
        # Use your actual write serializer. If you don't have a separate one,
        # ProductSerializer works (it already supports category_id as write-only).
        request=ProductSerializer,
        responses={201: OpenApiResponse(response=ProductSerializer)},
    ),
    update=extend_schema(
        summary="Replace product",
        tags=["Products"],
        request=ProductSerializer,
        responses={200: OpenApiResponse(response=ProductSerializer)},
    ),
    partial_update=extend_schema(
        summary="Update product (partial)",
        tags=["Products"],
        request=ProductSerializer,
        responses={200: OpenApiResponse(response=ProductSerializer)},
    ),
    destroy=extend_schema(
        summary="Delete product",
        tags=["Products"],
        responses={204: OpenApiResponse(description="Product deleted")},
    ),
)
class ProductViewSet(viewsets.ModelViewSet):
    """
    Products catalog with nested variants, media, and lightweight reviews.

    Public reads; privileged writes.
    """
    queryset = Product.objects.prefetch_related(
        "variants", "media", "reviews").all()
    serializer_class = ProductSerializer
    pagination_class = MediumResultsSetPagination
    filter_backends = [DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter]

    search_fields = ["name", "description"]
    filterset_fields = {"category": ["exact"], "price": [
        "gte", "lte"], "is_active": ["exact"]}
    ordering_fields = ["price", "name", "created_at"]
    ordering = ["-created_at"]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated(), RolePermission(Roles.privileged)()]
        return [permissions.AllowAny()]


# ========================= Product Variants =========================

@extend_schema_view(
    list=extend_schema(
        summary="List product variants",
        tags=["Products: Variants"],
        responses={200: OpenApiResponse(
            response=ProductVariantSerializer(many=True))},
    ),
    retrieve=extend_schema(
        summary="Get a product variant",
        tags=["Products: Variants"],
        responses={200: OpenApiResponse(response=ProductVariantSerializer)},
    ),
    create=extend_schema(
        summary="Create product variant",
        tags=["Products: Variants"],
        request=ProductVariantSerializer,
        responses={201: OpenApiResponse(response=ProductVariantSerializer)},
    ),
    update=extend_schema(
        summary="Replace product variant",
        tags=["Products: Variants"],
        request=ProductVariantSerializer,
        responses={200: OpenApiResponse(response=ProductVariantSerializer)},
    ),
    partial_update=extend_schema(
        summary="Update product variant (partial)",
        tags=["Products: Variants"],
        request=ProductVariantSerializer,
        responses={200: OpenApiResponse(response=ProductVariantSerializer)},
    ),
    destroy=extend_schema(
        summary="Delete product variant",
        tags=["Products: Variants"],
        responses={204: OpenApiResponse(description="Variant deleted")},
    ),
)
class ProductVariantViewSet(viewsets.ModelViewSet):
    """
    Variants belonging to products.

    Public reads; admin writes.
    """
    queryset = ProductVariant.objects.select_related("product").all()
    serializer_class = ProductVariantSerializer

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]


# ========================= Product Media =========================

@extend_schema_view(
    list=extend_schema(
        summary="List product media",
        tags=["Products: Media"],
        responses={200: OpenApiResponse(
            response=ProductMediaSerializer(many=True))},
    ),
    retrieve=extend_schema(
        summary="Get a product media item",
        tags=["Products: Media"],
        responses={200: OpenApiResponse(response=ProductMediaSerializer)},
    ),
    create=extend_schema(
        summary="Create product media",
        tags=["Products: Media"],
        request=ProductMediaSerializer,
        responses={201: OpenApiResponse(response=ProductMediaSerializer)},
    ),
    update=extend_schema(
        summary="Replace product media",
        tags=["Products: Media"],
        request=ProductMediaSerializer,
        responses={200: OpenApiResponse(response=ProductMediaSerializer)},
    ),
    partial_update=extend_schema(
        summary="Update product media (partial)",
        tags=["Products: Media"],
        request=ProductMediaSerializer,
        responses={200: OpenApiResponse(response=ProductMediaSerializer)},
    ),
    destroy=extend_schema(
        summary="Delete product media",
        tags=["Products: Media"],
        responses={204: OpenApiResponse(description="Media deleted")},
    ),
)
class ProductMediaViewSet(viewsets.ModelViewSet):
    """
    Media assets attached to products.

    Public reads; admin writes.
    """
    queryset = ProductMedia.objects.select_related("product").all()
    serializer_class = ProductMediaSerializer

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]


# ========================= Product Reviews =========================

@extend_schema_view(
    list=extend_schema(
        summary="List product reviews",
        description="Small-page pagination (max 10 per page).",
        tags=["Products: Reviews"],
        parameters=[_page_param_small, _page_size_small],
        responses={200: OpenApiResponse(
            response=ProductReviewSerializer(many=True))},
    ),
    retrieve=extend_schema(
        summary="Get a review",
        tags=["Products: Reviews"],
        responses={200: OpenApiResponse(response=ProductReviewSerializer)},
    ),
    create=extend_schema(
        summary="Create a review",
        tags=["Products: Reviews"],
        # user is taken from request in serializer.create()
        request=ProductReviewSerializer,
        responses={201: OpenApiResponse(response=ProductReviewSerializer)},
    ),
    update=extend_schema(
        summary="Replace a review",
        tags=["Products: Reviews"],
        request=ProductReviewSerializer,
        responses={200: OpenApiResponse(response=ProductReviewSerializer)},
    ),
    partial_update=extend_schema(
        summary="Update a review (partial)",
        tags=["Products: Reviews"],
        request=ProductReviewSerializer,
        responses={200: OpenApiResponse(response=ProductReviewSerializer)},
    ),
    destroy=extend_schema(
        summary="Delete a review",
        tags=["Products: Reviews"],
        responses={204: OpenApiResponse(description="Review deleted")},
    ),
)
class ProductReviewViewSet(viewsets.ModelViewSet):
    """
    Customer reviews. Auth required to create/update/delete; anyone can read.

    Pagination:
      SmallResultsSetPagination (page/page_size up to 10).
    """
    queryset = ProductReview.objects.select_related("user", "product").all()
    serializer_class = ProductReviewSerializer
    pagination_class = SmallResultsSetPagination

    def perform_create(self, serializer):
        """Attach the authenticated user to the review on creation."""
        serializer.save(user=self.request.user)

    def get_permissions(self):
        if self.action in ["update", "partial_update", "destroy", "create"]:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]
