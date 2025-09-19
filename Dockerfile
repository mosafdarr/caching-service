# Dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

WORKDIR /app

# System deps for psycopg2 (skip if SQLite only)
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry

# Layer caching for deps
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi --no-root

# App code
COPY . .

# FastAPI expects to find src/
ENV PYTHONPATH=/app/src

# Expose API port
EXPOSE 8000

# Use gunicorn + uvicorn workers (more resilient than bare uvicorn)
# worker count can be overridden at runtime via WORKERS env
ENV WORKERS=4
CMD sh -c "alembic upgrade head && \
    gunicorn src.index:app \
    -k uvicorn.workers.UvicornWorker \
    -w ${WORKERS} \
    -b 0.0.0.0:8000 \
    --access-logfile - \
    --error-logfile - \
    --timeout 60"
