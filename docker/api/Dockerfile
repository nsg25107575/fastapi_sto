# Build context for this image is the repository root (see docker-compose.yml
# `build.context: .`, resolved via --project-directory .), so all COPY paths below are
# relative to the project root, not this docker/api/ directory.

FROM python:3.14-slim AS base

# System deps:
# - build-essential + libmariadb-dev: needed to build the `mariadb`
#   python package (C extension against libmariadb)
# - curl: used by the container healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libmariadb-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (better layer caching)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy project source
COPY . .

# Entrypoint lives alongside this Dockerfile; make it executable.
COPY docker/api/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # Port the app listens on inside the container (overridable via .env)
    APP_PORT=8000 \
    # Number of uvicorn worker processes (tune to ~ 2 x CPU cores on the host)
    UVICORN_WORKERS=4 \
    # Max simultaneous in-flight requests per worker before 503-backpressure
    UVICORN_LIMIT_CONCURRENCY=1000 \
    # Pending-connection queue size (OS backlog) per worker
    UVICORN_BACKLOG=2048 \
    # How long to keep idle keep-alive connections open (seconds)
    UVICORN_KEEPALIVE=5

EXPOSE $APP_PORT

HEALTHCHECK --interval=10s --timeout=3s --start-period=15s --retries=5 \
    CMD sh -c 'curl -fsS "http://localhost:${APP_PORT}/docs" -o /dev/null' || exit 1

# entrypoint.sh waits for the database, applies Alembic migrations, then
# execs Uvicorn — see docker/api/entrypoint.sh for details.
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
