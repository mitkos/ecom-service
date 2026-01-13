from __future__ import annotations

import random
import uuid
from decimal import Decimal
from io import BytesIO

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from ecommerce.models import Category, Product

try:
    from PIL import Image
except Exception:  # pragma: no cover
    Image = None  # type: ignore


class Command(BaseCommand):
    help = "Seed development data for a food store: categories + products (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--products",
            type=int,
            default=40,
            help="Number of products to create (default: 40).",
        )
        parser.add_argument(
            "--with-images",
            action="store_true",
            help="Generate tiny placeholder images (requires Pillow).",
        )
        parser.add_argument(
            "--currency",
            type=str,
            default="EUR",
            help="Currency code for generated products (default: EUR).",
        )
        parser.add_argument(
            "--inactive-product-ratio",
            type=float,
            default=0.10,
            help="Fraction of generated products to mark inactive (default: 0.10).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        products_count: int = options["products"]
        with_images: bool = options["with_images"]
        currency: str = (options["currency"] or "EUR").upper()
        inactive_ratio: float = float(options["inactive_product_ratio"])

        if with_images and Image is None:
            self.stderr.write(
                self.style.ERROR(
                    "Pillow is not available. Install Pillow or omit --with-images."
                )
            )
            return

        rng = random.Random(42)

        # --- Categories (Food store tree) ---
        root = self._upsert_category(
            name="Food Store", slug="food-store", parent=None, position=1
        )

        fruits_veg = self._upsert_category(
            "Fruits & Vegetables", "fruits-vegetables", root, 10
        )
        dairy_eggs = self._upsert_category("Dairy & Eggs", "dairy-eggs", root, 20)
        meat_fish = self._upsert_category("Meat & Fish", "meat-fish", root, 30)
        bakery = self._upsert_category("Bakery", "bakery", root, 40)
        pantry = self._upsert_category("Pantry", "pantry", root, 50)
        beverages = self._upsert_category("Beverages", "beverages", root, 60)
        frozen = self._upsert_category("Frozen", "frozen", root, 70)
        snacks = self._upsert_category("Snacks", "snacks", root, 80)

        # Subcategories
        fresh_fruit = self._upsert_category("Fresh Fruit", "fresh-fruit", fruits_veg, 1)
        fresh_veg = self._upsert_category(
            "Fresh Vegetables", "fresh-vegetables", fruits_veg, 2
        )
        herbs = self._upsert_category("Herbs", "herbs", fruits_veg, 3)

        milk_yogurt = self._upsert_category(
            "Milk & Yogurt", "milk-yogurt", dairy_eggs, 1
        )
        cheese = self._upsert_category("Cheese", "cheese", dairy_eggs, 2)
        eggs = self._upsert_category("Eggs", "eggs", dairy_eggs, 3)

        poultry = self._upsert_category("Poultry", "poultry", meat_fish, 1)
        beef_pork = self._upsert_category("Beef & Pork", "beef-pork", meat_fish, 2)
        fish = self._upsert_category("Fish", "fish", meat_fish, 3)

        bread = self._upsert_category("Bread", "bread", bakery, 1)
        pastries = self._upsert_category("Pastries", "pastries", bakery, 2)

        pasta_rice = self._upsert_category("Pasta & Rice", "pasta-rice", pantry, 1)
        canned = self._upsert_category("Canned Goods", "canned-goods", pantry, 2)
        spices = self._upsert_category("Spices & Sauces", "spices-sauces", pantry, 3)

        water = self._upsert_category("Water", "water", beverages, 1)
        soft_drinks = self._upsert_category("Soft Drinks", "soft-drinks", beverages, 2)
        coffee_tea = self._upsert_category("Coffee & Tea", "coffee-tea", beverages, 3)

        ice_cream = self._upsert_category("Ice Cream", "ice-cream", frozen, 1)
        frozen_veg = self._upsert_category(
            "Frozen Vegetables", "frozen-vegetables", frozen, 2
        )
        ready_meals = self._upsert_category("Ready Meals", "ready-meals", frozen, 3)

        chips_nuts = self._upsert_category("Chips & Nuts", "chips-nuts", snacks, 1)
        chocolate = self._upsert_category("Chocolate", "chocolate", snacks, 2)
        biscuits = self._upsert_category("Biscuits", "biscuits", snacks, 3)

        leaf_categories = [
            fresh_fruit,
            fresh_veg,
            herbs,
            milk_yogurt,
            cheese,
            eggs,
            poultry,
            beef_pork,
            fish,
            bread,
            pastries,
            pasta_rice,
            canned,
            spices,
            water,
            soft_drinks,
            coffee_tea,
            ice_cream,
            frozen_veg,
            ready_meals,
            chips_nuts,
            chocolate,
            biscuits,
        ]

        # --- Product templates (food store) ---
        templates = [
            # Fruits
            ("Bananas", fresh_fruit, (1.49, 1.99, 2.49), "kg"),
            ("Apples (Golden)", fresh_fruit, (1.29, 1.79, 2.19), "kg"),
            ("Oranges", fresh_fruit, (1.59, 2.09, 2.69), "kg"),
            ("Strawberries", fresh_fruit, (2.99, 3.99, 4.99), "500g"),
            # Vegetables
            ("Tomatoes", fresh_veg, (1.79, 2.49, 2.99), "kg"),
            ("Cucumbers", fresh_veg, (1.39, 1.99, 2.49), "kg"),
            ("Potatoes", fresh_veg, (0.89, 1.19, 1.49), "kg"),
            ("Onions", fresh_veg, (0.99, 1.29, 1.69), "kg"),
            # Herbs
            ("Parsley", herbs, (0.49, 0.69, 0.89), "bunch"),
            ("Dill", herbs, (0.49, 0.69, 0.89), "bunch"),
            # Dairy/Eggs
            ("Milk 3.2% 1L", milk_yogurt, (1.39, 1.59, 1.79), "1L"),
            ("Greek Yogurt 400g", milk_yogurt, (1.49, 1.99, 2.29), "400g"),
            ("Cheddar Cheese 200g", cheese, (2.49, 2.99, 3.49), "200g"),
            ("White Cheese (Sirene) 400g", cheese, (3.49, 3.99, 4.49), "400g"),
            ("Eggs L (10 pcs)", eggs, (2.49, 2.99, 3.49), "10pcs"),
            # Meat/Fish
            ("Chicken Breast Fillet", poultry, (6.99, 7.99, 8.99), "kg"),
            ("Pork Shoulder", beef_pork, (7.49, 8.49, 9.49), "kg"),
            ("Minced Beef 500g", beef_pork, (3.99, 4.49, 4.99), "500g"),
            ("Salmon Fillet 250g", fish, (5.99, 6.99, 7.99), "250g"),
            ("Tuna Steak 200g", fish, (4.99, 5.99, 6.99), "200g"),
            # Bakery
            ("White Bread 700g", bread, (1.19, 1.39, 1.59), "700g"),
            ("Wholegrain Bread 500g", bread, (1.39, 1.59, 1.79), "500g"),
            ("Croissant Butter", pastries, (0.79, 0.99, 1.19), "pc"),
            ("Chocolate Muffin", pastries, (0.99, 1.19, 1.49), "pc"),
            # Pantry
            ("Spaghetti 500g", pasta_rice, (1.19, 1.49, 1.79), "500g"),
            ("Basmati Rice 1kg", pasta_rice, (2.49, 2.99, 3.49), "1kg"),
            ("Canned Tomatoes 400g", canned, (0.99, 1.19, 1.39), "400g"),
            ("Canned Beans 400g", canned, (1.09, 1.29, 1.49), "400g"),
            ("Olive Oil 1L", spices, (8.99, 10.99, 12.99), "1L"),
            ("Soy Sauce 250ml", spices, (1.49, 1.99, 2.49), "250ml"),
            # Beverages
            ("Mineral Water 1.5L", water, (0.59, 0.79, 0.99), "1.5L"),
            ("Sparkling Water 1.5L", water, (0.69, 0.89, 1.09), "1.5L"),
            ("Cola 2L", soft_drinks, (1.79, 2.19, 2.49), "2L"),
            ("Orange Juice 1L", soft_drinks, (1.99, 2.49, 2.99), "1L"),
            ("Ground Coffee 250g", coffee_tea, (2.99, 3.99, 4.99), "250g"),
            ("Black Tea 25 bags", coffee_tea, (1.79, 2.29, 2.79), "25bags"),
            # Frozen
            ("Ice Cream Vanilla 1L", ice_cream, (3.49, 3.99, 4.49), "1L"),
            ("Frozen Peas 450g", frozen_veg, (1.49, 1.79, 2.09), "450g"),
            ("Frozen Pizza Margherita", ready_meals, (2.99, 3.49, 3.99), "pc"),
            # Snacks
            ("Potato Chips 150g", chips_nuts, (1.49, 1.79, 2.19), "150g"),
            ("Roasted Peanuts 200g", chips_nuts, (1.29, 1.59, 1.99), "200g"),
            ("Milk Chocolate 100g", chocolate, (0.99, 1.29, 1.59), "100g"),
            ("Biscuits Butter 200g", biscuits, (1.09, 1.39, 1.69), "200g"),
        ]

        # --- Upsert products (idempotent by SKU) ---
        existing = Product.objects.count()
        created = 0
        updated = 0

        # Deterministic SKU pattern for seeded items
        # e.g. FOOD-0001 ... FOOD-0040
        for i in range(1, products_count + 1):
            sku = f"FOOD-{i:04d}"

            # pick template deterministically but varied
            name, category, price_candidates, unit = templates[(i - 1) % len(templates)]
            brand = rng.choice(
                [
                    "FreshFarm",
                    "DailyMart",
                    "GoodFood",
                    "KitchenCo",
                    "NatureLine",
                    "ValueChoice",
                ]
            )

            title = f"{name} ({brand})"
            slug = self._stable_product_slug(title, sku)
            price = Decimal(str(rng.choice(price_candidates)))

            is_active = rng.random() >= inactive_ratio

            obj, was_created = Product.objects.update_or_create(
                sku=sku,
                defaults={
                    "title": title,
                    "slug": slug,
                    "description": f"{name}. Brand: {brand}. Pack: {unit}. Seeded dev product ({sku}).",
                    "price": price,
                    "currency": currency,
                    "category": category,
                    "is_active": is_active,
                    "position": i,
                },
            )

            if was_created:
                created += 1
            else:
                updated += 1

            if with_images:
                self._ensure_placeholder_image(obj)

        self.stdout.write(self.style.SUCCESS("Food store dev seed complete."))
        self.stdout.write(f"Categories: {Category.objects.count()} (root: {root.id})")
        self.stdout.write(
            f"Products: total={Product.objects.count()} (created={created}, updated={updated}, preexisting={existing})"
        )
        if with_images:
            self.stdout.write("Images: placeholder images ensured for seeded products.")

    def _upsert_category(
        self, name: str, slug: str, parent: Category | None, position: int
    ) -> Category:
        obj, _ = Category.objects.update_or_create(
            parent=parent,
            slug=slug,
            defaults={
                "name": name,
                "is_active": True,
                "position": position,
            },
        )
        return obj

    def _stable_product_slug(self, title: str, sku: str) -> str:
        # stable + unique without querying: use sku suffix
        return f"{slugify(title)}-{sku.lower()}"

    def _ensure_placeholder_image(self, product: Product) -> None:
        if product.image:
            return
        if Image is None:
            return

        img = Image.new("RGB", (64, 64))
        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        filename = f"seed-{uuid.uuid4().hex}.png"
        product.image.save(filename, ContentFile(buf.read()), save=True)
