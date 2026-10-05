#!/bin/bash
# Smoke check: the database host/port the api container is configured with
# must be consistent AND actually reachable from inside the container.
#
# Regression guard for two real incidents:
#   1. DB_PORT was set to the HOST-side published port (e.g. 3310) while
#      MariaDB still listens on 3306 inside the Docker network, so the
#      entrypoint waited on "<db host>:3310" forever and the container
#      exited with "Database did not become reachable in time".
#   2. DATABASE_URL was built from ${DB_HOST} at Compose parse time (value
#      from .env) while the container's own DB_HOST was overridden in the
#      `environment:` block, so the entrypoint and the app used different
#      hosts.
#
# Usage (from the repo root, with the stack running):
#   bash tests/smoke/db_host_port_check.sh
# Override the compose command (e.g. for the CI stack) with DC:
#   DC="docker compose -p kws_station_api_ci -f docker/api/docker-compose.ci.yml --project-directory ." \
#     bash tests/smoke/db_host_port_check.sh
set -e

DC="${DC:-docker compose -f docker/api/docker-compose.yml --project-directory .}"

echo "Checking DB host/port consistency and reachability inside the api container..."

# -T: no TTY, so the heredoc below is passed to the container's stdin.
# shellcheck disable=SC2086  # DC is intentionally word-split.
$DC exec -T api python - <<'PY'
import os
import socket
import sys
from urllib.parse import urlsplit

errors = []

db_host = os.environ.get("DB_HOST", "")
db_port = os.environ.get("DB_PORT", "")
url = urlsplit(os.environ.get("DATABASE_URL", ""))

if not db_host:
    errors.append("DB_HOST is not set in the container.")
if not db_port.isdigit():
    errors.append("DB_PORT is missing or not a number: %r." % db_port)

# The app (DATABASE_URL) and the entrypoint (DB_HOST/DB_PORT) must point at
# the very same database.
if db_host and url.hostname != db_host:
    errors.append(
        "DATABASE_URL host (%r) differs from DB_HOST (%r)." % (url.hostname, db_host)
    )
if db_port.isdigit() and url.port != int(db_port):
    errors.append(
        "DATABASE_URL port (%r) differs from DB_PORT (%r)." % (url.port, db_port)
    )

# Reachability: the same TCP check the entrypoint performs.
if db_host and db_port.isdigit():
    try:
        with socket.create_connection((db_host, int(db_port)), timeout=5):
            pass
    except OSError as exc:
        errors.append(
            "Cannot connect to %s:%s (%s). DB_PORT must be the port MariaDB "
            "listens on INSIDE the Docker network (3306); the port published "
            "on the host belongs in DB_HOST_PORT." % (db_host, db_port, exc)
        )

if errors:
    for message in errors:
        print("FAIL: " + message)
    sys.exit(1)

print("PASS: DATABASE_URL, DB_HOST and DB_PORT agree, and %s:%s is reachable." % (db_host, db_port))
PY
