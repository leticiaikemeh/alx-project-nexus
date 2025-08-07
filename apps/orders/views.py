from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from apps.orders.models import Order, OrderItem, Cart, CartItem
from apps.orders.serializers import (
    OrderSerializer,
    OrderItemSerializer,
    CartSerializer,
    CartItemSerializer
)
from apps.authentication.permissions import (
    IsOwnerOrAdmin,
    CanShipOrders,
)
from apps.authentication.constants import Roles

class OrderViewSet(viewsets.ModelViewSet):
    """
    Customers can view and create their own orders.
    Admins and warehouse can update status.
    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin, CanShipOrders]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return self.queryset
        return self.queryset.filter(user=user)

    def perform_create(self, serializer):
        if not self.request.user.has_role(Roles.CUSTOMER):
            raise PermissionDenied("Only customers can place orders.")
        serializer.save(user=self.request.user)


class OrderItemViewSet(viewsets.ModelViewSet):
    """
    Only the owner of the order can manage items.
    """
    queryset = OrderItem.objects.select_related('order', 'product_variant')
    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        return self.queryset.filter(order__user=self.request.user)


class CartViewSet(viewsets.ModelViewSet):
    """
    Only one cart per user. Auto-linked to the requesting user.
    """
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        if Cart.objects.filter(user=self.request.user).exists():
            raise PermissionDenied("You already have a cart.")
        serializer.save(user=self.request.user)


class CartItemViewSet(viewsets.ModelViewSet):
    """
    Only allow interacting with your own cart items.
    """
    queryset = CartItem.objects.select_related('cart', 'product_variant')
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        return self.queryset.filter(cart__user=self.request.user)

    def perform_create(self, serializer):
        # prevent adding duplicate product_variants to cart
        cart = self.request.user.cart
        product_variant = serializer.validated_data.get('product_variant')

        if CartItem.objects.filter(cart=cart, product_variant=product_variant).exists():
            raise PermissionDenied("Product already in cart.")
        serializer.save(cart=cart)
