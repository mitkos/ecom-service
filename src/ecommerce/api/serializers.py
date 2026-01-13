from __future__ import annotations

from decimal import Decimal
from typing import Any

from rest_framework import serializers

from ecommerce.models import Category, Product


class CategorySerializer(serializers.ModelSerializer):
    """
    CRUD serializer for Category.
    """

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "slug",
            "parent",
            "is_active",
            "position",
        ]


class ProductSerializer(serializers.ModelSerializer):
    """
    CRUD serializer for Product.
    """

    class Meta:
        model = Product
        fields = [
            "id",
            "sku",
            "title",
            "slug",
            "description",
            "image",
            "price",
            "currency",
            "category",
            "is_active",
            "position",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate_price(self, value: Decimal) -> Decimal:
        if value is None:
            return value
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0.")
        return value

    def validate_currency(self, value: str) -> str:
        if not value or len(value) != 3:
            raise serializers.ValidationError(
                "Currency must be a 3-letter code (e.g. EUR)."
            )
        return value.upper()
