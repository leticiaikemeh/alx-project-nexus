# apps/orders/serializers.py
from __future__ import annotations

from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample

from .models import Order, OrderItem, Cart, CartItem
from apps.products.models import ProductVariant
from apps.products.serializers import ProductVariantSerializer
from apps.payments.models import Payment
from apps.core.models import Address
from apps.authentication.serializers import UserMinimalSerializer


# ---------- OpenAPI Examples ----------

ORDER_ITEM_EXAMPLE = OpenApiExample(
    name="OrderItem",
    summary="Example order item (read)",
    value={
        "id": 101,
        "product_variant": {
            "id": 501,
            "name": "T-Shirt – Large – Blue",
            "price": "19.99",
            "sku": "TSHIRT-L-BLU"
        },
        "quantity": 2,
        "price_at_order": "19.99"
    }
)

ORDER_EXAMPLE = OpenApiExample(
    name="Order",
    summary="Example order with items",
    value={
        "id": 42,
        "user": {"id": "uuid-1234", "email": "john@example.com"},
        "status": "pending",
        "total_amount": "39.98",
        "shipping_address": "John Doe, 123 Main St, Lagos",
        "payment": "TXN-2025-0001",
        "created_at": "2025-08-13T10:00:00Z",
        "updated_at": "2025-08-13T10:10:00Z",
        "items": [ORDER_ITEM_EXAMPLE.value]
    }
)

ORDER_CREATE_EXAMPLE = OpenApiExample(
    name="OrderCreate",
    summary="Request to create an order",
    value={
        "shipping_address": 301,
        "items": [
            {"product_variant": 501, "quantity": 2}
        ],
        "total_amount": "39.98"
    }
)


# ---------- READ SERIALIZERS ----------

@extend_schema_serializer(component_name="OrderItem", examples=[ORDER_ITEM_EXAMPLE])
class OrderItemSerializer(serializers.ModelSerializer):
    """
    Read-only representation of an item in an order.
    """
    product_variant = ProductVariantSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product_variant', 'quantity', 'price_at_order']
        read_only_fields = fields


@extend_schema_serializer(component_name="Order", examples=[ORDER_EXAMPLE])
class OrderSerializer(serializers.ModelSerializer):
    """
    Read-only representation of an order, including items, user, and linked payment.
    """
    items = OrderItemSerializer(many=True, read_only=True)
    user = UserMinimalSerializer(read_only=True)
    shipping_address = serializers.StringRelatedField()
    payment = serializers.StringRelatedField()

    class Meta:
        model = Order
        fields = [
            'id',
            'user',
            'status',
            'total_amount',
            'shipping_address',
            'payment',
            'created_at',
            'updated_at',
            'items',
        ]
        read_only_fields = ['created_at', 'updated_at', 'items', 'user']


# ---------- WRITE SERIALIZERS ----------

class OrderItemCreateSerializer(serializers.ModelSerializer):
    """
    Write serializer for adding an item to an order.
    """
    product_variant = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.all()
    )

    class Meta:
        model = OrderItem
        fields = ['product_variant', 'quantity']

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1.")
        return value


@extend_schema_serializer(component_name="OrderCreate", examples=[ORDER_CREATE_EXAMPLE])
class OrderCreateSerializer(serializers.ModelSerializer):
    """
    Write serializer for creating an order with one or more items.
    """
    items = OrderItemCreateSerializer(many=True)
    shipping_address = serializers.PrimaryKeyRelatedField(
        queryset=Order._meta.get_field(
            'shipping_address').related_model.objects.all()
    )

    class Meta:
        model = Order
        fields = ['shipping_address', 'items', 'total_amount']

    def validate(self, attrs):
        if not attrs.get('items'):
            raise serializers.ValidationError(
                "Order must contain at least one item.")
        return attrs

    def create(self, validated_data):
        """
        Create the order atomically:
        - Validates stock before decrementing.
        - Saves each order item with snapshot price.
        """
        items_data = validated_data.pop('items')
        user = self.context['request'].user

        with transaction.atomic():
            order = Order.objects.create(user=user, **validated_data)

            for item_data in items_data:
                product_variant = item_data['product_variant']
                quantity = item_data['quantity']

                # Check inventory
                if product_variant.stock_quantity < quantity:
                    raise ValidationError(
                        f"Insufficient stock for {product_variant}. Available: {product_variant.stock_quantity}"
                    )

                # Decrement inventory
                product_variant.stock_quantity -= quantity
                product_variant.save()

                OrderItem.objects.create(
                    order=order,
                    product_variant=product_variant,
                    quantity=quantity,
                    price_at_order=product_variant.price_override or product_variant.product.price
                )

        return order


# ---------- CART SERIALIZERS ----------

class CartItemSerializer(serializers.ModelSerializer):
    """
    Read-only representation of an item in a cart.
    """
    product_variant = ProductVariantSerializer(read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'product_variant', 'quantity']
        read_only_fields = fields


class CartSerializer(serializers.ModelSerializer):
    """
    Read-only representation of a user's shopping cart.
    """
    items = CartItemSerializer(many=True, read_only=True)
    user = UserMinimalSerializer(read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'user', 'created_at', 'updated_at', 'items']
        read_only_fields = fields
