# ecommerce/urls.py (project)
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from apps.authentication import urls as auth_urls

urlpatterns = [
    path("admin/", admin.site.urls),

    # OpenAPI schema & docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/swagger/",
         SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/docs/redoc/",
         SpectacularRedocView.as_view(url_name="schema"), name="redoc"),

    # Mount authentication resources at /api/v1/
    path(
        "api/v1/",
        include((auth_urls.resource_urlpatterns, "authentication"),
                namespace="auth-resources"),
    ),

    # Mount auth endpoints at /api/v1/auth/
    path(
        "api/v1/auth/",
        include((auth_urls.auth_urlpatterns, "authentication"),
                namespace="auth-endpoints"),
    ),

    # Other apps — ensure their internal urls don't double-prefix
    path("api/v1/", include("apps.products.urls")),
    path("api/v1/", include("apps.orders.urls")),
    path("api/v1/", include("apps.payments.urls")),
    path("api/v1/", include("apps.notifications.urls")),
    path("api/v1/", include("apps.core.urls")),

    # Health
    path("healthz/", lambda request: HttpResponse("ok")),
]
