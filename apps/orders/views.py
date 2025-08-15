# apps/orders/views.py
from __future__ import annotations

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiResponse,
)

from apps.orders.models import Order, OrderItem, Cart, CartItem
from apps.orders.serializers import (
    OrderSerializer,
    OrderItemSerializer,
    CartSerializer,
    CartItemSerializer,
    OrderCreateSerializer,
)
from apps.authentication.permissions import (
    IsOwnerOrAdmin,
    CanShipOrders,
)
from apps.authentication.constants import Roles


@extend_schema_view(
    list=extend_schema(
        summary="List my orders (admins see all)",
        description=(
            "Returns orders visible to the caller.\n\n"
            "- **Customers**: only their own orders\n"
            "- **Admins/Warehouse (via permissions)**: all orders\n"
        ),
        tags=["Orders"],
        responses={200: OpenApiResponse(response=OrderSerializer(many=True))},
    ),
    retrieve=extend_schema(
        summary="Retrieve an order",
        tags=["Orders"],
        responses={200: OpenApiResponse(
            response=OrderSerializer), 404: OpenApiResponse(description="Not found")},
    ),
    create=extend_schema(
        summary="Create an order",
        description=(
            "Create a new order for the authenticated **customer**.\n\n"
            "Business rules:\n"
            "1) Only users with role `CUSTOMER` can create orders.\n"
            "2) At least one item is required.\n"
            "3) Stock is verified and decremented atomically."
        ),
        tags=["Orders"],
        request=OrderCreateSerializer,
        responses={201: OpenApiResponse(response=OrderSerializer), 400: OpenApiResponse(
            description="Validation error")},
    ),
    update=extend_schema(
        summary="Update an order (restricted)",
        description="Status/administrative updates typically restricted to Admin/Warehouse.",
        tags=["Orders"],
        responses={200: OpenApiResponse(response=OrderSerializer), 400: OpenApiResponse(
            description="Validation error")},
    ),
    partial_update=extend_schema(
        summary="Partially update an order (restricted)",
        description="Patch specific fields (e.g., status) if permitted.",
        tags=["Orders"],
        responses={200: OpenApiResponse(response=OrderSerializer), 400: OpenApiResponse(
            description="Validation error")},
    ),
    destroy=extend_schema(
        summary="Delete an order (typically disallowed)",
        description="Dangerous operation; keep for admin/testing only if your policy allows it.",
        tags=["Orders"],
        responses={204: OpenApiResponse(
            description="Deleted"), 403: OpenApiResponse(description="Forbidden")},
    ),
)
class OrderViewSet(viewsets.ModelViewSet):
    """
    Orders API.
    """
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin, CanShipOrders]

    # NEW: let Spectacular infer the model
    queryset = Order.objects.none()

    def get_queryset(self):
        # NEW: guard for schema generation
        if getattr(self, "swagger_fake_view", False):
            return Order.objects.none()

        user = self.request.user
        base_qs = (
            Order.objects
            .select_related("user", "shipping_address", "payment")
            .prefetch_related("items__product_variant")
        )
        return base_qs if getattr(user, "is_staff", False) else base_qs.filter(user=user)

    def get_serializer_class(self):
        return OrderCreateSerializer if self.action == "create" else OrderSerializer

    def perform_create(self, serializer):
        if not self.request.user.has_role(Roles.CUSTOMER):
            raise PermissionDenied("Only customers can place orders.")
        serializer.save(user=self.request.user)


@extend_schema_view(
    list=extend_schema(
        summary="List my order items",
        description="Returns order items that belong to the caller's orders.",
        tags=["Order Items"],
        responses={200: OpenApiResponse(
            response=OrderItemSerializer(many=True))},
    ),
    retrieve=extend_schema(
        summary="Retrieve an order item",
        tags=["Order Items"],
        responses={200: OpenApiResponse(
            response=OrderItemSerializer), 404: OpenApiResponse(description="Not found")},
    ),
    create=extend_schema(
        summary="Create an order item",
        description="Create an item under an owned order if your policy allows modifying items directly.",
        tags=["Order Items"],
        request=OrderItemSerializer,  # if you prefer a separate write serializer, swap here
        responses={201: OpenApiResponse(response=OrderItemSerializer), 400: OpenApiResponse(
            description="Validation error")},
    ),
    update=extend_schema(
        summary="Update an order item",
        tags=["Order Items"],
        responses={200: OpenApiResponse(response=OrderItemSerializer), 400: OpenApiResponse(
            description="Validation error")},
    ),
    partial_update=extend_schema(
        summary="Partially update an order item",
        tags=["Order Items"],
        responses={200: OpenApiResponse(response=OrderItemSerializer)},
    ),
    destroy=extend_schema(
        summary="Delete an order item",
        tags=["Order Items"],
        responses={204: OpenApiResponse(description="Deleted")},
    ),
)
class OrderItemViewSet(viewsets.ModelViewSet):
    """
    Order Items API.
    Only the owner of the parent order can manage items (enforced by `IsOwnerOrAdmin` and queryset filter).
    """
    queryset = OrderItem.objects.select_related(
        "order__user", "product_variant", "product_variant__product")
    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        # NEW: guard
        if getattr(self, "swagger_fake_view", False):
            return OrderItem.objects.none()
        return self.queryset.filter(order__user=self.request.user)


@extend_schema_view(
    list=extend_schema(
        summary="Get my cart (singleton)",
        description="Returns the caller's cart. System enforces one cart per user.",
        tags=["Cart"],
        # list because ModelViewSet list returns a collection
        responses={200: OpenApiResponse(response=CartSerializer(many=True))},
    ),
    retrieve=extend_schema(
        summary="Retrieve a cart",
        tags=["Cart"],
        responses={200: OpenApiResponse(
            response=CartSerializer), 404: OpenApiResponse(description="Not found")},
    ),
    create=extend_schema(
        summary="Create my cart",
        description="Create a cart for the caller. Fails if a cart already exists.",
        tags=["Cart"],
        request=CartSerializer,  # if you have a write serializer, swap it here
        responses={201: OpenApiResponse(response=CartSerializer), 403: OpenApiResponse(
            description="Already exists")},
    ),
    update=extend_schema(
        summary="Update my cart",
        tags=["Cart"],
        responses={200: OpenApiResponse(response=CartSerializer)},
    ),
    partial_update=extend_schema(
        summary="Partially update my cart",
        tags=["Cart"],
        responses={200: OpenApiResponse(response=CartSerializer)},
    ),
    destroy=extend_schema(
        summary="Delete my cart",
        tags=["Cart"],
        responses={204: OpenApiResponse(description="Deleted")},
    ),
)
class CartViewSet(viewsets.ModelViewSet):
    """
    Cart API.
    Singleton per user; auto-linked to the requesting user on create.
    """
    queryset = Cart.objects.select_related(
        "user").prefetch_related("items__product_variant")
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        # NEW: guard
        if getattr(self, "swagger_fake_view", False):
            return Cart.objects.none()
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        if Cart.objects.filter(user=self.request.user).exists():
            raise PermissionDenied("You already have a cart.")
        serializer.save(user=self.request.user)


@extend_schema_view(
    list=extend_schema(
        summary="List my cart items",
        description="Items within the caller's cart(s).",
        tags=["Cart Items"],
        responses={200: OpenApiResponse(
            response=CartItemSerializer(many=True))},
    ),
    retrieve=extend_schema(
        summary="Retrieve a cart item",
        tags=["Cart Items"],
        responses={200: OpenApiResponse(
            response=CartItemSerializer), 404: OpenApiResponse(description="Not found")},
    ),
    create=extend_schema(
        summary="Add item to my cart",
        description="Add a product variant to the caller's cart. Fails if the item already exists.",
        tags=["Cart Items"],
        request=CartItemSerializer,  # if you have a separate write serializer, swap here
        responses={201: OpenApiResponse(response=CartItemSerializer), 403: OpenApiResponse(
            description="Duplicate item")},
    ),
    update=extend_schema(
        summary="Update a cart item",
        tags=["Cart Items"],
        responses={200: OpenApiResponse(response=CartItemSerializer)},
    ),
    partial_update=extend_schema(
        summary="Partially update a cart item",
        tags=["Cart Items"],
        responses={200: OpenApiResponse(response=CartItemSerializer)},
    ),
    destroy=extend_schema(
        summary="Remove item from my cart",
        tags=["Cart Items"],
        responses={204: OpenApiResponse(description="Deleted")},
    ),
)
class CartItemViewSet(viewsets.ModelViewSet):
    """
    Cart Items API.
    Only the owner of the cart may interact with its items (enforced by `IsOwnerOrAdmin` and queryset filter).
    """
    queryset = CartItem.objects.select_related(
        "cart__user", "product_variant", "product_variant__product")
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        # NEW: guard
        if getattr(self, "swagger_fake_view", False):
            return CartItem.objects.none()
        return self.queryset.filter(cart__user=self.request.user)

    def perform_create(self, serializer):
        cart = self.request.user.cart
        product_variant = serializer.validated_data.get("product_variant")

        if CartItem.objects.filter(cart=cart, product_variant=product_variant).exists():
            raise PermissionDenied("Product already in cart.")
        serializer.save(cart=cart)
