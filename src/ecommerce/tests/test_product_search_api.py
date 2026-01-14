from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from ecommerce.models import Category, Product

pytestmark = pytest.mark.django_db


def _url() -> str:
    return reverse("product-search")


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def categories():
    """
    Food store tree:
      Food Store
        Fruits & Vegetables
          Fresh Fruit
            Citrus
    """
    root = Category.objects.create(
        name="Food Store",
        slug="food-store",
        parent=None,
        is_active=True,
        position=1,
    )
    fruits_veg = Category.objects.create(
        name="Fruits & Vegetables",
        slug="fruits-vegetables",
        parent=root,
        is_active=True,
        position=10,
    )
    fresh_fruit = Category.objects.create(
        name="Fresh Fruit",
        slug="fresh-fruit",
        parent=fruits_veg,
        is_active=True,
        position=1,
    )
    citrus = Category.objects.create(
        name="Citrus",
        slug="citrus",
        parent=fresh_fruit,
        is_active=True,
        position=1,
    )

    return root, fruits_veg, fresh_fruit, citrus


@pytest.fixture
def products(categories):
    root, fruits_veg, fresh_fruit, citrus = categories

    # Active products
    p1 = Product.objects.create(
        sku="FOOD-0001",
        title="Bananas (FreshFarm)",
        slug="bananas-freshfarm-food-0001",
        description="Bananas, kg.",
        price="2.20",
        currency="EUR",
        category=fresh_fruit,
        is_active=True,
        position=1,
    )
    p2 = Product.objects.create(
        sku="FOOD-0002",
        title="Oranges (NatureLine)",
        slug="oranges-natureline-food-0002",
        description="Oranges, kg.",
        price="2.80",
        currency="EUR",
        category=citrus,
        is_active=True,
        position=2,
    )
    p3 = Product.objects.create(
        sku="FOOD-0003",
        title="Milk 3.2% 1L (DailyMart)",
        slug="milk-3-2-1l-dailymart-food-0003",
        description="Milk 1L.",
        price="1.60",
        currency="EUR",
        category=root,
        is_active=True,
        position=3,
    )

    # Inactive product (should be hidden by default)
    p4 = Product.objects.create(
        sku="FOOD-0004",
        title="Strawberries 500g (FreshFarm)",
        slug="strawberries-500g-freshfarm-food-0004",
        description="Strawberries 500g.",
        price="4.50",
        currency="EUR",
        category=fresh_fruit,
        is_active=False,
        position=4,
    )

    return p1, p2, p3, p4


def test_search_defaults_to_is_active_true(api_client, products):
    r = api_client.get(_url())
    assert r.status_code == 200
    data = r.json()
    results = data["results"]
    skus = {p["sku"] for p in results}

    assert "FOOD-0001" in skus
    assert "FOOD-0002" in skus
    assert "FOOD-0003" in skus
    assert "FOOD-0004" not in skus  # inactive excluded


def test_search_can_return_only_inactive(api_client, products):
    r = api_client.get(_url(), {"is_active": "false"})
    assert r.status_code == 200
    results = r.json()["results"]
    skus = {p["sku"] for p in results}

    assert skus == {"FOOD-0004"}


def test_search_q_matches_title_or_exact_sku(api_client, products):
    # title icontains
    r1 = api_client.get(_url(), {"q": "milk"})
    assert r1.status_code == 200
    skus1 = {p["sku"] for p in r1.json()["results"]}
    assert skus1 == {"FOOD-0003"}

    # sku exact-ish (iexact)
    r2 = api_client.get(_url(), {"q": "food-0002"})
    assert r2.status_code == 200
    skus2 = {p["sku"] for p in r2.json()["results"]}
    assert skus2 == {"FOOD-0002"}


def test_search_sku_exact(api_client, products):
    r = api_client.get(_url(), {"sku": "FOOD-0001"})
    assert r.status_code == 200
    results = r.json()["results"]
    assert [p["sku"] for p in results] == ["FOOD-0001"]


def test_search_price_range(api_client, products):
    # Should match Oranges (2.80) but not Bananas (2.20) nor Milk (1.60)
    r = api_client.get(_url(), {"min_price": "2.50", "max_price": "3.00"})
    assert r.status_code == 200
    results = r.json()["results"]
    assert [p["sku"] for p in results] == ["FOOD-0002"]


def test_search_category_tree(api_client, categories, products):
    root, fruits_veg, fresh_fruit, citrus = categories

    # Without tree: only products directly in Fresh Fruit (active only)
    r1 = api_client.get(_url(), {"category": fresh_fruit.id})
    assert r1.status_code == 200
    skus1 = {p["sku"] for p in r1.json()["results"]}
    assert skus1 == {"FOOD-0001"}  # FOOD-0004 is inactive

    # With tree: Fresh Fruit + Citrus descendants (active only)
    r2 = api_client.get(_url(), {"category": fresh_fruit.id, "category_tree": "1"})
    assert r2.status_code == 200
    skus2 = {p["sku"] for p in r2.json()["results"]}
    assert skus2 == {"FOOD-0001", "FOOD-0002"}  # still excludes inactive FOOD-0004


def test_search_ordering_whitelist(api_client, products):
    # By -price should order active products: Oranges (2.80), Bananas (2.20), Milk (1.60)
    r = api_client.get(_url(), {"ordering": "-price"})
    assert r.status_code == 200
    results = r.json()["results"]
    assert [p["sku"] for p in results] == ["FOOD-0002", "FOOD-0001", "FOOD-0003"]


def test_search_invalid_ordering_field(api_client, products):
    r = api_client.get(_url(), {"ordering": "does_not_exist"})
    assert r.status_code == 400
    body = r.json()
    assert "ordering" in body
