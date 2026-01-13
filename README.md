
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
docker compose up --build

## Creating superuser for Django admin
docker compose exec web python manage.py createsuperuser

## Useful links

# API
http://localhost:8000/api  
# API Docs
http://localhost:8000/api/docs/
# Django Admin
http://localhost:8000/admin/


## Media storage

For local development, uploaded media files are stored on the filesystem
and persisted via a Docker volume.

In a production environment, media files would typically be stored in
object storage (e.g. S3-compatible storage) and served via a CDN.
This is intentionally out of scope for this assignment.
