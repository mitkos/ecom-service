from django.db import models
from datetime import date
import os
import uuid


def product_image_upload_to(instance: "Product", filename: str) -> str:
    """
    Store uploads under products/YYYY/MM/DD/ with a safe unique name.
    """
    today = date.today()
    base, ext = os.path.splitext(filename)
    ext = ext.lower()[:10]  # keep extension reasonable
    return f"products/{today:%Y/%m/%d}/{uuid.uuid4().hex}{ext}"


class Category(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, default="")
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="children",
        on_delete=models.SET_NULL,
    )

    is_active = models.BooleanField(default=True)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["slug"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["position"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["parent", "name"], name="uniq_category_name_per_parent"
            )
        ]

        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self) -> str:
        return self.name

    def descendant_ids(self) -> list[int]:
        """
        Returns IDs of this category and all ACTIVE descendants.
        Inactive categories are intentionally excluded.
        """
        if not self.is_active:
            return []

        ids: list[int] = []
        to_visit: list[int] = [self.id]

        while to_visit:
            current_id = to_visit.pop()
            ids.append(current_id)

            children = Category.objects.filter(
                parent_id=current_id,
                is_active=True,
            ).values_list("id", flat=True)

            to_visit.extend(children)

        return ids


class Product(models.Model):
    sku = models.CharField(max_length=64, unique=True)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, default="")
    description = models.TextField(blank=True)

    image = models.ImageField(
        upload_to=product_image_upload_to,
        blank=True,
        null=True,
    )

    price = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="EUR")

    category = models.ForeignKey(
        Category,
        related_name="products",
        on_delete=models.PROTECT,
    )

    is_active = models.BooleanField(default=True)
    position = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["sku"]),
            models.Index(fields=["slug"]),
            models.Index(fields=["title"]),
            models.Index(fields=["price"]),
            models.Index(fields=["category"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["position"]),
        ]

    def __str__(self) -> str:
        return f"{self.sku} - {self.title}"
