# syntax=docker/dockerfile:1
FROM node:20-alpine AS frontend-deps

WORKDIR /app/frontend

COPY project/frontend/package.json project/frontend/package-lock.json ./

RUN --mount=type=cache,target=/root/.npm \
    npm ci

FROM frontend-deps AS frontend-builder

WORKDIR /app/frontend

COPY project/frontend/ ./

RUN npm run build

FROM python:3.14-slim AS python-deps

RUN apt-get update && apt-get install -y \
    git \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

ENV POETRY_VERSION=2.5.1
RUN python -m pip install "poetry==${POETRY_VERSION}"

WORKDIR /app/project

COPY pyproject.toml poetry.lock /app/

ARG INSTALL_DEV=false
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=cache,target=/tmp/poetry_cache \
    POETRY_CACHE_DIR=/tmp/poetry_cache \
    pip install --upgrade pip \
    && cd /app \
    && poetry config virtualenvs.create false \
    && poetry install --only=main --no-root \
    && if [ "$INSTALL_DEV" = "true" ]; then \
        poetry install --only=dev --no-root; \
    fi

FROM python-deps

WORKDIR /app/project

COPY project/ /app/project/
COPY --from=frontend-builder /app/staticfiles/frontend /app/project/staticfiles/frontend
# Дублируем фронтенд в /app/frontend-dist — эта директория не перекрывается
# bind-томом staticfiles. docker-compose.yml копирует её в staticfiles/frontend при старте.
COPY --from=frontend-builder /app/staticfiles/frontend /app/frontend-dist
