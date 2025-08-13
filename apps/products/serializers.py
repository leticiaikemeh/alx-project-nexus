from typing import Any, Dict
from rest_framework import serializers
from .models import (
    Category,
    Product,
    ProductVariant,
    ProductMedia,
    ProductReview,
)


class CategorySerializer(serializers.ModelSerializer):
    """
    Category model projection.

    Fields:
        id (int): PK.
        name (str): Category name.
        parent (int|null): Parent category ID (nullable).
    """
    class Meta:
        model = Category
        fields = ["id", "name", "parent"]


class ProductMediaSerializer(serializers.ModelSerializer):
    """
    Media attached to a product.

    Fields:
        id (int): PK.
        url (str): Public media URL.
        media_type (str): Media kind, e.g. 'image', 'video'.
    """
    class Meta:
        model = ProductMedia
        fields = ["id", "url", "media_type"]


class ProductVariantSerializer(serializers.ModelSerializer):
    """
    Variant for a product (e.g., size/color SKU).

    Fields:
        id (int): PK.
        name (str): Variant name.
        stock_quantity (int): Inventory count.
        price_override (str|null): Override price (decimal-as-string), optional.
        sku (str): Variant SKU.
    """
    class Meta:
        model = ProductVariant
        fields = ["id", "name", "stock_quantity", "price_override", "sku"]


class ProductReviewSerializer(serializers.ModelSerializer):
    """
    Review authored by a user for a product.

    Create:
        - `user` is taken from request context; do not supply in payload.

    Fields:
        id (int)
        user (int, read-only): auto-filled from request.
        user_email (str, read-only)
        product (int)
        product_name (str, read-only)
        rating (int)
        comment (str)
        created_at (datetime, read-only)
    """

    user_email = serializers.EmailField(source="user.email", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = ProductReview
        fields = [
            "id",
            "user",
            "user_email",
            "product",
            "product_name",
            "rating",
            "comment",
            "created_at",
        ]
        read_only_fields = ["user", "user_email", "product_name", "created_at"]

    def create(self, validated_data: Dict[str, Any]):
        """
        Create a review for the authenticated user.
        """
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class ProductSerializer(serializers.ModelSerializer):
    """
    Product with nested category, variants, media, and reviews.

    Write:
        - Provide `category_id` to set the category.

    Read:
        - `category` (nested), `variants` (nested), `media` (nested), `reviews` (nested).

    Notes:
        - Decimal fields are serialized as strings.
    """

    # Read
    category = CategorySerializer(read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    media = ProductMediaSerializer(many=True, read_only=True)
    reviews = ProductReviewSerializer(
        many=True, read_only=True, source="reviews")

    # Write
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source="category", write_only=True
    )

    # Optional: expose nested reviews (assumes related_name='reviews')
    # If your model uses a different related name, adjust source accordingly.
    reviews = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "price",
            "sku",
            "is_active",
            "created_at",
            "updated_at",
            "category",
            "category_id",
            "variants",
            "media",
            "reviews",
        ]
        read_only_fields = ["created_at", "updated_at"]
