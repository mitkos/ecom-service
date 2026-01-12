
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app/src

RUN apt-get update \
 && apt-get install -y build-essential libpq-dev \
 && rm -rf /var/lib/apt/lists/*

COPY requirements/ /app/requirements/
RUN pip install --upgrade pip \
 && pip install -r /app/requirements/dev.txt


COPY src/ /app/src/
