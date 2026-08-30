# Mandala Health — container image
FROM python:3.13-slim

WORKDIR /app

# Version visibility: git hash/tag injected by CI (docker-publish workflow).
# Without it (local builds) the app falls back to "dev".
ARG GIT_VERSION=dev
ENV APP_VERSION=${GIT_VERSION} \
    APP_GIT_HASH=${GIT_VERSION}

# Install deps first for layer caching
COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv && uv sync --frozen --no-dev --no-install-project

COPY app/ app/
COPY deploy/ deploy/

# Local diary database (SQLite) lives in /app/data (mounted as a volume)
RUN mkdir -p /app/data

EXPOSE 8020
CMD [".venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8020"]
