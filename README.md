
# E-commerce Product Service

Mini interview project implementing a product catalog service.

## Tech Stack
- Python 3.12
- Django + Django REST Framework
- PostgreSQL
- Docker & Docker Compose

## Features
- Product CRUD
- Category hierarchy (parent/child)
- Search & filtering (name, SKU, price range, category)
- Django Admin
- API documentation (Swagger)

## Local setup

- bash
git clone https://github.com/mitkos/ecom-service.git
cd ecom-service
docker compose up -d --build
docker compose exec web python /app/src/manage.py migrate

## Creating superuser for Django admin
docker compose exec web python manage.py createsuperuser


## API
http://localhost:8000/api/v1/  


# API Docs

Swagger UI:
http://localhost:8000/api/docs/

ReDoc:
http://localhost:8000/api/redoc/

OpenAPI schema:
http://localhost:8000/api/schema/


# Django Admin
http://localhost:8000/admin/


## Media storage

For local development, uploaded media files are stored on the filesystem
and persisted via a Docker volume.

In a production environment, media files would typically be stored in
object storage (e.g. S3-compatible storage) and served via a CDN.
This is intentionally out of scope for this assignment.


## Testing

Unit tests are written for the product search functionality only,
as required by the assignment.

Run tests:
docker compose run --rm web pytest

Seed dev data for manual testing:
docker compose exec web python /app/src/manage.py seed_dev


## Product search examples

Search by text:
http://localhost:8000/api/v1/products/search/?q=milk

Search by price range:
http://localhost:8000/api/v1/products/search/?min_price=2&max_price=5

Search by category subtree:
http://localhost:8000/api/v1/products/search/?category=1&category_tree=1


## Design decisions

- Product and Category IDs are database-generated auto-increment fields.
  The API exposes them as read-only to prevent client-side control.
- SKU and slug are explicit fields and are not auto-generated.
- Search is implemented as a dedicated endpoint, separate from CRUD,
  to keep responsibilities clear and allow more flexible query logic.
- By default, search returns only active products from active categories
  to avoid leaking hidden catalog data.
- Migrations are run explicitly as a setup step.
  They are not executed automatically on container startup.
  In a production setup, migrations would typically be run as a controlled
  deployment step (CI/CD job or one-off task), rather than on every app start.
