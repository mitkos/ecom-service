from __future__ import annotations

from decimal import Decimal, InvalidOperation

from django.db.models import Q

from rest_framework import filters, status, viewsets, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.validators import UniqueValidator

from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema


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
    search_fields = ["title", "sku", "slug"]
    ordering_fields = ["position", "price", "created_at", "updated_at", "title", "id"]
    ordering = ["position", "-created_at"]

    @extend_schema(
        summary="Search products",
        description=(
            "Search and filter products using query parameters. "
            "By default, only active products from active categories are returned. "
            "Supports text search (title or SKU), exact SKU lookup, price range filtering, "
            "category filtering with optional subtree inclusion, safe ordering, and pagination."
        ),
        parameters=[
            OpenApiParameter(
                name="q",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Text search: matches title (icontains) OR sku (iexact).",
                examples=[
                    # examples are optional; if your spectacular version supports them, this is nice
                ],
            ),
            OpenApiParameter(
                name="sku",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Exact SKU match (case-insensitive).",
            ),
            OpenApiParameter(
                name="title",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Title contains (case-insensitive).",
            ),
            OpenApiParameter(
                name="min_price",
                type=OpenApiTypes.DECIMAL,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Minimum price (inclusive). Example: 2.50",
            ),
            OpenApiParameter(
                name="max_price",
                type=OpenApiTypes.DECIMAL,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Maximum price (inclusive). Example: 10.00",
            ),
            OpenApiParameter(
                name="category",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Category ID to filter by.",
            ),
            OpenApiParameter(
                name="category_tree",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                required=False,
                description="If true, includes products from active descendant categories.",
            ),
            OpenApiParameter(
                name="is_active",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter by active flag. Defaults to true.",
            ),
            OpenApiParameter(
                name="ordering",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Comma-separated ordering. Allowed: position, price, created_at, updated_at, title, id. Prefix with '-' for desc.",
            ),
            # Pagination params (Swagger will often show these automatically, but being explicit is fine)
            OpenApiParameter(
                name="page",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Page number (pagination).",
            ),
            OpenApiParameter(
                name="page_size",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Page size (if enabled).",
            ),
        ],
        responses=ProductSerializer(
            many=True
        ),  # OK, but paginated response is better; see note below
    )
    @action(detail=False, methods=["get"], url_path="search")
    def search(self, request):
        """
        GET /api/v1/products/search/

        Query params:
          q=             -> title icontains OR sku iexact
          sku=           -> sku exact
          title=         -> title icontains
          min_price=     -> price >=
          max_price=     -> price <=
          category=      -> category id
          category_tree=1 -> include category descendants
          is_active=true/false (default true)
          ordering=price,-created_at,position
        """
        qs = Product.objects.all().select_related("category")

        # is_active default true (common catalog behavior)
        is_active_raw = request.query_params.get("is_active", "true").lower()
        if is_active_raw in ("true", "1", "yes", "y", "on"):
            qs = qs.filter(is_active=True)
        elif is_active_raw in ("false", "0", "no", "n", "off"):
            qs = qs.filter(is_active=False)
        else:
            return Response(
                {"is_active": "Invalid boolean value."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        q = request.query_params.get("q")
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(sku__iexact=q))

        sku = request.query_params.get("sku")
        if sku:
            qs = qs.filter(sku__iexact=sku)

        title = request.query_params.get("title")
        if title:
            qs = qs.filter(title__icontains=title)

        # price filters
        min_price = request.query_params.get("min_price")
        if min_price:
            try:
                qs = qs.filter(price__gte=Decimal(min_price))
            except (InvalidOperation, ValueError):
                return Response(
                    {"min_price": "Invalid decimal value."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        max_price = request.query_params.get("max_price")
        if max_price:
            try:
                qs = qs.filter(price__lte=Decimal(max_price))
            except (InvalidOperation, ValueError):
                return Response(
                    {"max_price": "Invalid decimal value."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # category filtering
        category_id = request.query_params.get("category")
        category_tree = request.query_params.get("category_tree", "0").lower() in (
            "1",
            "true",
            "yes",
            "y",
            "on",
        )

        if category_id:
            try:
                category_obj = Category.objects.get(pk=int(category_id))
            except (ValueError, Category.DoesNotExist):
                return Response(
                    {"category": "Invalid category id."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if category_tree:
                ids = category_obj.descendant_ids()
                qs = qs.filter(category_id__in=ids)
            else:
                qs = qs.filter(category=category_obj)

        # ordering (reuse DRF OrderingFilter)
        ordering_param = request.query_params.get("ordering")
        if ordering_param:
            # Validate ordering fields manually (avoid arbitrary field ordering)
            allowed = set(self.ordering_fields)
            requested = [p.strip() for p in ordering_param.split(",") if p.strip()]
            normalized = []
            for item in requested:
                key = item.lstrip("-")
                if key not in allowed:
                    return Response(
                        {"ordering": f"Invalid ordering field: {key}"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                normalized.append(item)
            qs = qs.order_by(*normalized)
        else:
            qs = qs.order_by(*self.ordering)

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)
