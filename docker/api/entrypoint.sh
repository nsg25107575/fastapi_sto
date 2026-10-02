#!/bin/sh
set -e

# Entrypoint for the api container.
#
# 1. Waits for the database to accept connections (depends_on/healthcheck
#    already handles most of this, but we double-check here so the
#    entrypoint is safe even when run standalone).
#    Also keeps pip up to date and ensures uv is available (dev tooling
#    used by `make deps-update`, not an application dependency).
# 2. Applies all pending Alembic migrations.
# 3. Starts Uvicorn with the configured number of workers.

: "${DB_HOST:=db}"
: "${DB_PORT:=3306}"
: "${APP_PORT:=8000}"
: "${UVICORN_WORKERS:=4}"
: "${UVICORN_LIMIT_CONCURRENCY:=1000}"
: "${UVICORN_BACKLOG:=2048}"
: "${UVICORN_KEEPALIVE:=5}"

echo "[entrypoint] Ensuring pip is up to date and uv is installed..."
pip install --upgrade pip
pip install uv

echo "[entrypoint] Waiting for database at ${DB_HOST}:${DB_PORT}..."

attempt=0
max_attempts=60
until python -c "
import socket, sys
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(2)
try:
    s.connect(('${DB_HOST}', ${DB_PORT}))
except OSError:
    sys.exit(1)
finally:
    s.close()
"; do
    attempt=$((attempt + 1))
    if [ "$attempt" -ge "$max_attempts" ]; then
        echo "[entrypoint] Database did not become reachable in time, exiting." >&2
        exit 1
    fi
    sleep 1
done

echo "[entrypoint] Database is reachable. Applying migrations..."
alembic upgrade head

echo "[entrypoint] Migrations applied. Starting Uvicorn on port ${APP_PORT} with ${UVICORN_WORKERS} worker(s)..."
exec uvicorn main:app \
    --host 0.0.0.0 \
    --port "$APP_PORT" \
    --workers "$UVICORN_WORKERS" \
    --limit-concurrency "$UVICORN_LIMIT_CONCURRENCY" \
    --backlog "$UVICORN_BACKLOG" \
    --timeout-keep-alive "$UVICORN_KEEPALIVE" \
    --proxy-headers \
    --no-server-header
