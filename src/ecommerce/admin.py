from django.contrib import admin

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "parent")
    search_fields = ("name",)
    list_filter = ("parent",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "sku", "title", "price", "category", "updated_at")
    search_fields = ("sku", "title")
    list_filter = ("category",)
