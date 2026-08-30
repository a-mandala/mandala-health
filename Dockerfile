# Mandala Health — container image
FROM python:3.13-slim

WORKDIR /app

# Install deps first for layer caching
COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv && uv sync --frozen --no-dev --no-install-project

COPY app/ app/
COPY deploy/ deploy/
COPY data/seed_foods.json data/seed_foods.json

# Local food database (SQLite) lives in /app/data (mounted as a volume)
RUN mkdir -p /app/data

EXPOSE 8020
CMD [".venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8020"]
