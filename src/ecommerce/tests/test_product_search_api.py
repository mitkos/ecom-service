from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from ecommerce.models import Category, Product


pytestmark = pytest.mark.django_db


def _url() -> str:
    # router action name: product-search if basename="product"
    return reverse("product-search")


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def categories():
    """
    Tree:
      root
        child
          grandchild
    """
    root = Category.objects.create(
        name="Root", slug="root", parent=None, is_active=True, position=1
    )
    child = Category.objects.create(
        name="Child", slug="child", parent=root, is_active=True, position=1
    )
    grand = Category.objects.create(
        name="Grand", slug="grand", parent=child, is_active=True, position=1
    )
    return root, child, grand


@pytest.fixture
def products(categories):
    root, child, grand = categories

    p1 = Product.objects.create(
        sku="SKU-AAA",
        title="Red Shirt",
        slug="red-shirt",
        description="",
        price="10.00",
        currency="EUR",
        category=root,
        is_active=True,
        position=1,
    )
    p2 = Product.objects.create(
        sku="SKU-BBB",
        title="Blue Shirt",
        slug="blue-shirt",
        description="",
        price="20.00",
        currency="EUR",
        category=child,
        is_active=True,
        position=2,
    )
    p3 = Product.objects.create(
        sku="SKU-CCC",
        title="Green Pants",
        slug="green-pants",
        description="",
        price="30.00",
        currency="EUR",
        category=grand,
        is_active=False,
        position=3,
    )
    return p1, p2, p3


def test_search_defaults_to_is_active_true(api_client, products):
    r = api_client.get(_url())
    assert r.status_code == 200
    data = r.json()
    # paginated response
    results = data["results"]
    skus = {p["sku"] for p in results}
    assert "SKU-AAA" in skus
    assert "SKU-BBB" in skus
    assert "SKU-CCC" not in skus  # inactive


def test_search_can_include_inactive(api_client, products):
    r = api_client.get(_url(), {"is_active": "false"})
    assert r.status_code == 200
    results = r.json()["results"]
    skus = {p["sku"] for p in results}
    assert skus == {"SKU-CCC"}


def test_search_q_matches_title_or_exact_sku(api_client, products):
    r1 = api_client.get(_url(), {"q": "shirt"})
    assert r1.status_code == 200
    skus1 = {p["sku"] for p in r1.json()["results"]}
    assert skus1 == {"SKU-AAA", "SKU-BBB"}

    r2 = api_client.get(_url(), {"q": "sku-bbb"})
    assert r2.status_code == 200
    skus2 = {p["sku"] for p in r2.json()["results"]}
    assert skus2 == {"SKU-BBB"}


def test_search_price_range(api_client, products):
    r = api_client.get(_url(), {"min_price": "15", "max_price": "25"})
    assert r.status_code == 200
    results = r.json()["results"]
    assert [p["sku"] for p in results] == ["SKU-BBB"]


def test_search_category_tree(api_client, categories, products):
    root, child, grand = categories

    # without tree => only root category products
    r1 = api_client.get(_url(), {"category": root.id})
    assert r1.status_code == 200
    skus1 = {p["sku"] for p in r1.json()["results"]}
    assert skus1 == {"SKU-AAA"}

    # with tree => root + descendants, but still default is_active=true
    r2 = api_client.get(_url(), {"category": root.id, "category_tree": "1"})
    assert r2.status_code == 200
    skus2 = {p["sku"] for p in r2.json()["results"]}
    assert skus2 == {"SKU-AAA", "SKU-BBB"}  # SKU-CCC is inactive


def test_search_ordering_whitelist(api_client, products):
    r = api_client.get(_url(), {"ordering": "-price"})
    assert r.status_code == 200
    results = r.json()["results"]
    assert [p["sku"] for p in results] == [
        "SKU-BBB",
        "SKU-AAA",
    ]  # active only, 20 then 10


def test_search_invalid_ordering_field(api_client, products):
    r = api_client.get(_url(), {"ordering": "does_not_exist"})
    assert r.status_code == 400
    assert "ordering" in r.json()
