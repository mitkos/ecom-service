from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="children",
        on_delete=models.SET_NULL,
    )

    class Meta:
        indexes = [
            models.Index(fields=["name"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["parent", "name"], name="uniq_category_name_per_parent"
            )
        ]

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    sku = models.CharField(max_length=64, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    price = models.DecimalField(max_digits=12, decimal_places=2)

    category = models.ForeignKey(
        Category,
        related_name="products",
        on_delete=models.PROTECT,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["sku"]),
            models.Index(fields=["title"]),
            models.Index(fields=["price"]),
            models.Index(fields=["category"]),
        ]

    def __str__(self) -> str:
        return f"{self.sku} - {self.title}"
