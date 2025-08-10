from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Category, Product, ProductVariant, ProductMedia, ProductReview

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'parent')
    search_fields = ('name',)
    list_filter = ('parent',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'sku', 'price', 'is_active', 'category', 'created_at')
    search_fields = ('name', 'sku')
    list_filter = ('is_active', 'category', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'name', 'sku', 'stock_quantity', 'price_override')
    search_fields = ('product__name', 'name', 'sku')
    list_filter = ('product',)

@admin.register(ProductMedia)
class ProductMediaAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'media_type', 'url')
    search_fields = ('product__name', 'url')
    list_filter = ('media_type',)

@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'product', 'rating', 'created_at')
    search_fields = ('user__email', 'product__name')
    list_filter = ('rating', 'created_at')
    readonly_fields = ('created_at',)
