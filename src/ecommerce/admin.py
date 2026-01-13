from django.contrib import admin
from django.utils.html import format_html

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "parent")
    search_fields = ("name",)
    list_filter = ("parent",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "sku",
        "title",
        "price",
        "category",
        "updated_at",
    )
    search_fields = ("sku", "title")
    list_filter = ("category",)

    readonly_fields = ("image_preview", "created_at", "updated_at")

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "sku",
                    "title",
                    "description",
                    "category",
                    "price",
                )
            },
        ),
        (
            "Image",
            {
                "fields": (
                    "image",
                    "image_preview",
                )
            },
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    def image_preview(self, obj):
        if not obj.image:
            return "—"
        return format_html(
            '<img src="{}" style="max-height: 150px; max-width: 250px; object-fit: contain;" />',
            obj.image.url,
        )

    image_preview.short_description = "Preview"
