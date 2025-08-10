from rest_framework import serializers
from .models import (
    Category,
    Product,
    ProductVariant,
    ProductMedia,
    ProductReview
)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'parent']


class ProductMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductMedia
        fields = ['id', 'url', 'media_type']


class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ['id', 'name', 'stock_quantity', 'price_override', 'sku']


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True
    )

    variants = ProductVariantSerializer(many=True, read_only=True)
    media = ProductMediaSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'description',
            'price',
            'sku',
            'is_active',
            'created_at',
            'updated_at',
            'category',
            'category_id',
            'variants',
            'media',
            'reviews'
        ]
        read_only_fields = ['created_at', 'updated_at']


class ProductReviewSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = ProductReview
        fields = ['id', 'user', 'user_email', 'product', 'product_name', 'rating', 'comment', 'created_at']
        read_only_fields = ['user', 'user_email', 'product_name', 'created_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
