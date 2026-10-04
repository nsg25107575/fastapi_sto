#!/bin/bash
set -e

echo "Checking DATABASE_URL structure inside the api container..."
docker compose -f docker/api/docker-compose.yml --project-directory . exec api \
  python -c "
import os, re

url = os.environ.get('DATABASE_URL', '')
# Verify the URL contains a user:password@ segment before the host,
# without ever printing the actual credentials.
pattern = r'^mariadb\+mariadbconnector://[^:/@]+:[^@]+@[^:/]+:\d+/[^/]+$'
if not re.match(pattern, url):
    print('FAIL: DATABASE_URL is missing the user:password@ segment or has an unexpected shape.')
    raise SystemExit(1)
print('PASS: DATABASE_URL has the expected user:password@host:port/db shape.')
"

echo "Checking that SQLAlchemy can actually authenticate and connect..."
docker compose -f docker/api/docker-compose.yml --project-directory . exec api \
  python -c "
from sqlalchemy import create_engine, text
import os

engine = create_engine(os.environ['DATABASE_URL'])
with engine.connect() as conn:
    result = conn.execute(text('SELECT 1'))
    assert result.scalar() == 1
print('PASS: successfully authenticated and connected as the application DB user.')
"