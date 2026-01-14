from django.contrib import admin
from django.utils.html import format_html

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "parent", "position", "is_active")
    list_filter = ("is_active", "parent")
    search_fields = ("name", "slug")
    ordering = ("position", "name", "id")

    # Admin UI convenience only (does NOT affect API)
    prepopulated_fields = {"slug": ("name",)}

    # Better UX for big datasets
    list_per_page = 50
    list_select_related = ("parent",)

    fieldsets = (
        (None, {"fields": ("name", "slug", "parent")}),
        ("Visibility & ordering", {"fields": ("is_active", "position")}),
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "sku",
        "title",
        "slug",
        "category",
        "price",
        "currency",
        "position",
        "is_active",
        "updated_at",
    )
    list_filter = ("is_active", "category", "currency")
    search_fields = ("sku", "title", "slug")
    ordering = ("position", "id")
    list_per_page = 50
    list_select_related = ("category",)

    prepopulated_fields = {"slug": ("title",)}

    readonly_fields = ("image_preview", "created_at", "updated_at")

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "sku",
                    "title",
                    "slug",
                    "description",
                )
            },
        ),
        (
            "Category & pricing",
            {
                "fields": (
                    "category",
                    ("price", "currency"),
                )
            },
        ),
        (
            "Visibility & ordering",
            {
                "fields": (
                    "is_active",
                    "position",
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

    def image_preview(self, obj: Product) -> str:
        if not obj.image:
            return "—"
        return format_html(
            '<img src="{}" style="max-height: 150px; max-width: 250px; object-fit: contain;" />',
            obj.image.url,
        )

    image_preview.short_description = "Preview"
