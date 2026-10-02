# Installation Guide

This guide covers two ways to run KWS Station API: with **Docker** (recommended)
or **natively** on Python 3.14 with a local MariaDB instance.

## Prerequisites

- **Docker** 24+ and **Docker Compose** v2 (for the Docker setup), or
- **Python 3.14+** and a running **MariaDB** server (for the native setup)
- `make` (optional, but recommended — the project ships a `Makefile` with
  shortcuts for every command below)

## 1. Clone the Repository

```bash
git clone <repository-url>
cd kws_station_api
```

## 2. Configure Environment Variables

Copy the example file and fill in real values:

```bash
cp .env.example .env
```

| Variable                    | Description                                                 | Example                       |
|-----------------------------|-------------------------------------------------------------|-------------------------------|
| `APP_NAME`                  | Application/service name                                    | `station-api`                 |
| `APP_PORT`                  | Port the API listens on (host & container)                  | `8000`                        |
| `APP_ENV`                   | Environment name (`development`/`production`)               | `development`                 |
| `APP_TIMEZONE`              | Timezone used for timestamps                                | `Europe/Kyiv`                 |
| `APP_NEAREST_STATION_LIMIT` | Default limit for "nearest stations" search                 | `10`                          |
| `DB_HOST`                   | Database host (use `db` for Docker, `localhost` for native) | `db`                          |
| `DB_PORT`                   | Database port exposed on the host                           | `3306`                        |
| `DB_NAME`                   | Database name                                               | `station_db`                  |
| `DB_USER`                   | Database user                                               | `station_user`                |
| `DB_PASSWORD`               | Database user password                                      | *(secret)*                    |
| `DB_ROOT_PASSWORD`          | MariaDB root password (Docker only)                         | *(secret)*                    |
| `JWT_SECRET_KEY`            | Secret used to sign JWT tokens                              | *(secret, generate your own)* |
| `JWT_EXPIRES_IN`            | JWT expiration, in seconds                                  | `3600`                        |
| `COOKIES_SECRET_KEY`        | Secret used to sign cookies                                 | *(secret)*                    |
| `COOKIES_SECURE`            | Send cookies only over HTTPS                                | `False` (dev) / `True` (prod) |
| `MAX_COOKIE_AGE_IN_DAYS`    | Cookie lifetime, in days                                    | `7`                           |

> **Security note:** never commit a real `.env` file. Generate strong,
> unique values for `JWT_SECRET_KEY`, `COOKIES_SECRET_KEY`, `DB_PASSWORD`,
> and `DB_ROOT_PASSWORD` before deploying anywhere beyond local development.

The application resolves the database connection in this order (see `../config/config.py`):
1. An explicit `DATABASE_URL`, if set (used automatically inside Docker).
2. Otherwise, it is assembled from `DB_USER`, `DB_PASSWORD`, `DB_HOST`,
   `DB_PORT`, and `DB_NAME`.
3. Falls back to a local SQLite file if neither is available.

## 3. Run with Docker (Recommended)

Build the images and start the stack (API + MariaDB) in the background:

```bash
make docker-up-build
```

Equivalent raw command:

```bash
docker compose -f docker/api/docker-compose.yml --project-directory . up -d --build
```

> `--project-directory .` is required when running the raw command — it
> tells Compose to resolve `.env`, build context, and volume paths relative
> to the repository root, even though the compose file itself lives under
> `docker/api/`. The `make` targets already include this flag, so you only
> need it when invoking `docker compose` directly.

Migrations are applied **automatically** by `docker/api/entrypoint.sh` every
time the `api` container starts (it waits for the database, runs
`alembic upgrade head`, then starts Uvicorn) — no manual migration step is
required for the Docker workflow. If you need to apply migrations without
restarting the API (e.g. in CI), you can still run:

```bash
make migrate-up
```

Check that everything is running:

```bash
make docker-ps
make docker-logs
```

The API is now available at `http://localhost:${APP_PORT}` (e.g.
`http://localhost:8000`), with interactive docs at `/docs`.

To stop the stack:

```bash
make docker-down
```

### Docker Stack Details

All Docker assets live under [`docker/api/`](../docker/api/) rather than the
project root, so the stack can be extended later with additional services
(e.g. `docker/worker/`, `docker/nginx/`) without cluttering the repo root.

- **`docker/api/Dockerfile`** — image definition
  (`python:3.14-slim`), runs Uvicorn with multiple workers tuned for
  concurrent load (`UVICORN_WORKERS`, `UVICORN_LIMIT_CONCURRENCY`, etc. —
  configurable via environment variables).
- **`docker/api/entrypoint.sh`** — container entrypoint: waits for the `db`
  service to accept TCP connections, runs `alembic upgrade head`, then execs
  Uvicorn. Safe to re-run on every container start/restart.
- **`docker/api/docker-compose.yml`** — the actual stack definition (`api` +
  `db`). Build context is the project root (`../..`), so `COPY` paths inside
  the Dockerfile are relative to the repo root, not `docker/api/`.
- **`db` service** — `mariadb:latest`, tuned for higher concurrency
  (`max_connections`, InnoDB buffer pool size, I/O threads), with a
  persistent named volume (`kws_station_db_data`) and a healthcheck that
  the `api` service waits on before starting.
- Both services have CPU/memory limits and log rotation configured in
  `docker/api/docker-compose.yml` — adjust them to match your host's resources.

## 4. Run Natively (without Docker)

1. Make sure a MariaDB server is running and reachable, and that you have
   created the database/user referenced in your `.env`.
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   > Installing the `mariadb` package requires the MariaDB Connector/C
   > development headers (e.g. `libmariadb-dev` on Debian/Ubuntu,
   > `mariadb-connector-c-devel` on RHEL/Alpine, or the MariaDB Connector/C
   > installer on Windows) to be available on your system before running
   > `pip install`.
4. Apply migrations:
   ```bash
   alembic upgrade head
   ```
5. Start the development server:
   ```bash
   uvicorn main:app --reload
   ```

## 5. Dependency Tooling (`pip` & `uv`)

Two tools manage Python packages for this project — **neither is listed
in `pyproject.toml`'s `dependencies`**, because they are developer/build
tooling, not something the application imports or runs with at runtime:

- **`pip`** — comes bundled with every Python installation/virtualenv (`python -m venv .venv` already includes it). You
  normally don't need
  to install it separately; if it's ever missing from a venv, restore it
  with:
  ```bash
  python -m ensurepip --upgrade
  ```
- **`uv`** ([astral-sh/uv](https://github.com/astral-sh/uv)) — only
  needed to compile `requirements.txt` from `pyproject.toml`
  (`make deps-update`, `make deps-update-package`). It is **not** required
  to run the app, run tests, or build the Docker image. Install it once
  into your virtualenv with:
  ```bash
  pip install uv
  ```
  The `make deps-update*` targets also auto-install `uv` into the active
  venv on first use if it isn't already present, so this manual step is
  optional.

## 6. Keeping Dependencies Up to Date

`requirements.txt` is a **compiled, pinned lockfile** generated from the
version ranges declared in `pyproject.toml` (via `uv pip compile`; see
[Dependency Tooling](#5-dependency-tooling-pip--uv) above for how `uv`
itself is installed).
Do not hand-edit it — regenerate it instead:

```bash
# Upgrade everything within the constraints declared in pyproject.toml
make deps-update

# Upgrade a single package only
make deps-update-package package="fastapi"

# See which installed packages have newer versions available
make deps-outdated
```

After regenerating, rebuild the image (`make docker-up-build`) so the
container picks up the updated `requirements.txt`.

A [`renovate.json`](../renovate.json) config is included at the repo root
for teams that run a self-hosted [Renovate](https://docs.renovatebot.com/)
bot/runner against their Git server — it will open update PRs/MRs
automatically on a weekly schedule. It is inactive unless such a runner is
configured.

## 7. Verifying the Installation

- Open `http://localhost:${APP_PORT}/docs` in a browser — you should see the
  Swagger UI.
- Run the test suite:
  ```bash
  pytest
  ```

## Troubleshooting

| Symptom                                        | Likely Cause                            | Fix                                                                                     |
|------------------------------------------------|-----------------------------------------|-----------------------------------------------------------------------------------------|
| `api` container exits immediately              | Missing/incorrect `.env` values         | Check `make docker-logs` and verify `.env` against `.env.example`                       |
| `pip install` fails building `mariadb` package | Missing MariaDB Connector/C dev headers | Install `libmariadb-dev` (or platform equivalent) before `pip install`                  |
| API can't reach the database                   | Wrong `DB_HOST` for your setup          | Use `DB_HOST=db` for Docker, `DB_HOST=localhost` (or your DB host) for native runs      |
| `alembic upgrade head` fails to connect        | Database not ready yet                  | Wait for the `db` container healthcheck to pass, or start the DB first in native setups |
