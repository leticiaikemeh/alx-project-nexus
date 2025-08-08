from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Order, OrderItem, Cart, CartItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product_variant', 'quantity', 'price_at_order')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total_amount', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__email', 'status')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'product_variant', 'quantity', 'price_at_order')
    search_fields = ('order__user__email', 'product_variant__product__name')
    list_filter = ('product_variant',)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'updated_at')
    search_fields = ('user__email',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'cart', 'product_variant', 'quantity')
    search_fields = ('cart__user__email', 'product_variant__product__name')
    list_filter = ('product_variant',)
