from rest_framework import serializers
from .models import Order, OrderItem, Cart, CartItem
from apps.products.models import ProductVariant
from apps.products.serializers import ProductVariantSerializer
from apps.payments.models import Payment
from apps.core.models import Address
from apps.authentication.serializers import UserMinimalSerializer
from rest_framework import serializers
from django.db import transaction
from rest_framework.exceptions import ValidationError

class OrderItemSerializer(serializers.ModelSerializer):
    product_variant = ProductVariantSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product_variant', 'quantity', 'price_at_order']
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
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

class OrderItemCreateSerializer(serializers.ModelSerializer):
    product_variant = serializers.PrimaryKeyRelatedField(queryset=ProductVariant.objects.all())

    class Meta:
        model = OrderItem
        fields = ['product_variant', 'quantity']

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1.")
        return value


class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderItemCreateSerializer(many=True)
    shipping_address = serializers.PrimaryKeyRelatedField(queryset=Order._meta.get_field('shipping_address').related_model.objects.all())

    class Meta:
        model = Order
        fields = ['shipping_address', 'items', 'total_amount']

    def validate(self, attrs):
        if not attrs.get('items'):
            raise serializers.ValidationError("Order must contain at least one item.")
        return attrs

    def create(self, validated_data):
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

class CartItemSerializer(serializers.ModelSerializer):
    product_variant = ProductVariantSerializer(read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'product_variant', 'quantity']
        read_only_fields = fields


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    user = UserMinimalSerializer(read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'user', 'created_at', 'updated_at', 'items']
        read_only_fields = fields
