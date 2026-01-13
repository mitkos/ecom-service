from __future__ import annotations

from rest_framework import filters, viewsets
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from ecommerce.models import Category, Product

from .serializers import CategorySerializer, ProductSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    """
    /api/v1/categories/
    """

    queryset = Category.objects.all().select_related("parent")
    serializer_class = CategorySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        "name",
    ]
    ordering_fields = [
        "position",
        "name",
    ]
    ordering = [
        "position",
    ]


class ProductViewSet(viewsets.ModelViewSet):
    """
    /api/v1/products/
    """

    sku = serializers.CharField(
        validators=[
            UniqueValidator(
                queryset=Product.objects.all(),
                message="Product with this SKU already exists.",
            )
        ]
    )

    slug = serializers.SlugField(
        validators=[
            UniqueValidator(
                queryset=Product.objects.all(),
                message="Product with this slug already exists.",
            )
        ]
    )

    queryset = Product.objects.all().select_related("category")
    serializer_class = ProductSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "sku"]
    ordering_fields = [
        "position",
        "price",
        "created_at",
        "title",
    ]
    ordering = ["position", "-created_at"]
