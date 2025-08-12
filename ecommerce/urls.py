from django.contrib import admin
from django.urls import path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions


schema_view = get_schema_view(

    openapi.Info(

        title="Ecommerce API",

        default_version="v1",

        description="API documentation for Ecommerce",

        terms_of_service="https://nexus-commerce.store/terms/",

        contact=openapi.Contact(email="support@nexus-commerce.store"),

        license=openapi.License(name="BSD License"),

    ),

    public=True,

    permission_classes=(permissions.AllowAny,),

)


urlpatterns = [

    path('admin/', admin.site.urls),


 # Modular app routes

    path('api/auth/', include('apps.authentication.urls')),

    path('api/products/', include('apps.products.urls')),

    path('api/orders/', include('apps.orders.urls')),

    path('api/payments/', include('apps.payments.urls')),

    path('api/notifications/', include('apps.notifications.urls')),

    path('api/core/', include('apps.core.urls')),


 # Health

    path('healthz/', lambda request: __import__('django').http.HttpResponse('ok')),


    path('docs/swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='swagger-ui'),

    path('docs/openapi.json', schema_view.without_ui(cache_timeout=0), name='openapi-schema'),  # Ensure this line exists for openapi.json

]

