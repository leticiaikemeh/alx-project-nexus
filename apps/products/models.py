# Fully fleshed-out Django models for each of the entities in their respective apps.

from pathlib import Path

BASE_DIR = Path("ecommerce_project_full")
MODELS = {
    "authentication": {
        "User": """from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)
""",
        "Role": """from django.db import models

class Role(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name
""",
        "UserRole": """from django.db import models
from .models import User, Role

class UserRole(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
"""
    },
    "products": {
        "Category": """from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name
""",
        "Product": """from django.db import models
from .category import Category

class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    sku = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
""",
        "ProductVariant": """from django.db import models
from .product import Product

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    stock_quantity = models.PositiveIntegerField()
    price_override = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sku = models.CharField(max_length=100)
""",
        "ProductMedia": """from django.db import models
from .product import Product

class ProductMedia(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    url = models.URLField()
    media_type = models.CharField(max_length=50)
""",
        "ProductReview": """from django.db import models
from authentication.models import User
from .product import Product

class ProductReview(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    rating = models.IntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
"""
    }
}

# Write models to file
for app, model_defs in MODELS.items():
    app_dir = BASE_DIR / "apps" / app
    app_dir.mkdir(parents=True, exist_ok=True)
    models_file = app_dir / "models.py"
    with models_file.open("w") as mf:
        for _, model_code in model_defs.items():
            mf.write(model_code + "\n\n")

import ace_tools as tools; tools.display_dataframe_to_user(name="Apps with Full Models", dataframe=None)
