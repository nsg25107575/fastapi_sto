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

| Variable                    | Description                                                                                                                          | Example                                      |
|-----------------------------|--------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------|
| `APP_NAME`                  | Application/service name                                                                                                             | `station-api`                                |
| `APP_PORT`                  | Port the API listens on (host & container)                                                                                           | `8000`                                       |
| `APP_ENV`                   | Environment name (`development`/`production`)                                                                                        | `development`                                |
| `APP_TIMEZONE`              | Timezone used for timestamps                                                                                                         | `Europe/Kyiv`                                |
| `APP_NEAREST_STATION_LIMIT` | Default limit for "nearest stations" search                                                                                          | `10`                                         |
| `GEOCODING_BASE_URL`        | Address-to-coordinates provider endpoint (used by `POST /stations`)                                                                  | `https://nominatim.openstreetmap.org/search` |
| `GEOCODING_USER_AGENT`      | User-Agent sent to the geocoding provider (required by Nominatim's usage policy)                                                     | `kws-station-api/1.0`                        |
| `GEOCODING_TIMEOUT`         | Geocoding HTTP request timeout, in seconds                                                                                           | `5`                                          |
| `DB_HOST`                   | Database host (the DB container name `kws_station_db` for Docker, `localhost` for native). Also used as the DB `container_name`      | `kws_station_db`                             |
| `DB_PORT`                   | Port MariaDB listens on **inside** the Docker network (used by the API and `entrypoint.sh`). Keep `3306` for Docker                  | `3306`                                       |
| `DB_HOST_PORT`              | Port published on the **host** for the DB container (only for access from the host, e.g. a DB client). Not used by the API container | `3310`                                       |
| `DB_NAME`                   | Database name                                                                                                                        | `station_db`                                 |
| `DB_USER`                   | Database user                                                                                                                        | `station_user`                               |
| `DB_PASSWORD`               | Database user password                                                                                                               | *(secret)*                                   |
| `DB_ROOT_PASSWORD`          | MariaDB root password (Docker only)                                                                                                  | *(secret)*                                   |
| `JWT_SECRET_KEY`            | Secret used to sign JWT tokens                                                                                                       | *(secret, generate your own)*                |
| `JWT_EXPIRES_IN`            | JWT expiration, in seconds                                                                                                           | `3600`                                       |
| `COOKIES_SECRET_KEY`        | Secret used to sign cookies                                                                                                          | *(secret)*                                   |
| `COOKIES_SECURE`            | Send cookies only over HTTPS                                                                                                         | `False` (dev) / `True` (prod)                |
| `MAX_COOKIE_AGE_IN_DAYS`    | Cookie lifetime, in days                                                                                                             | `7`                                          |

> **Database ports — don't mix them up.** `DB_PORT` is the port *inside*
> the Docker network (always `3306` for the MariaDB image), while
> `DB_HOST_PORT` is only the host-side port in the `ports:` mapping
> (`DB_HOST_PORT:3306`). Setting `DB_PORT=3310` makes the API wait for
> `kws_station_db:3310`, where nothing listens, and the container exits
> with `Database did not become reachable in time`.

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
make up-build
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
make ps
make logs
```

The API is now available at `http://localhost:${APP_PORT}` (e.g.
`http://localhost:8000`), with interactive docs at `/docs`.

To stop the stack:

```bash
make down
```

### Docker Stack Details

All Docker assets live under [`docker/api/`](../docker/api/) rather than the
project root, so the stack can be extended later with additional services
(e.g. `docker/worker/`, `docker/nginx/`) without cluttering the repo root.

- **`docker/api/Dockerfile`** — image definition
  (`python:3.14-slim`), runs Uvicorn with multiple workers tuned for
  concurrent load (`UVICORN_WORKERS`, `UVICORN_LIMIT_CONCURRENCY`, etc. —
  configurable via environment variables).
- **`docker/api/entrypoint.sh`** — container entrypoint: waits until
  `${DB_HOST}:${DB_PORT}` accepts TCP connections, runs `alembic upgrade head`,
  then execs Uvicorn. Safe to re-run on every container start/restart.
- **`docker/api/docker-compose.yml`** — the actual stack definition (`api` +
  `db`). Build context is the project root (`../..`), so `COPY` paths inside
  the Dockerfile are relative to the repo root, not `docker/api/`.
- **`db` service** — `mariadb:latest`, tuned for higher concurrency
  (`max_connections`, InnoDB buffer pool size, I/O threads), with a
  persistent named volume (`kws_station_db_data`) and a healthcheck that
  the `api` service waits on before starting. The container is named after
  `DB_HOST` (default `kws_station_db`), and the API reaches it by that name.
  MariaDB always listens on `3306` inside the container; `DB_HOST_PORT`
  (default `3310`) is only the port published on the host.
- Both services have CPU/memory limits and log rotation configured in
  `docker/api/docker-compose.yml` — adjust them to match your host's resources.

### Other Compose Files

| File                                 | Purpose                                                                                                                                                                                                                                         | Ports / names                                                                                         |
|--------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| `docker/api/docker-compose.yml`      | Base stack for local development (bind-mounts the repo for hot reload). Used by all `make` targets                                                                                                                                              | API `APP_PORT`, DB host port `DB_HOST_PORT` (`3310`), containers `kws_station_api` / `kws_station_db` |
| `docker/api/docker-compose.prod.yml` | Production **override**, applied on top of the base file. Joins the external `kws_default` network so Nginx Proxy Manager can reach the API by name, and pins `DB_HOST` to the unique container name instead of the ambiguous service name `db` | Same as the base file                                                                                 |
| `docker/api/docker-compose.ci.yml`   | Standalone CI stack (Gitea Actions): no bind mount, own project name (`-p kws_station_api_ci`), network and volume, so it can't tear down production                                                                                            | API `8001`, DB host port `3307`, containers `kws_station_api_ci` / `kws_station_db_ci`                |

Production deployment:

```bash
docker compose -f docker/api/docker-compose.yml -f docker/api/docker-compose.prod.yml --project-directory . up -d --build
```

The `kws_default` network must already exist on the host (it is created by
the main `kws` stack). To preview the resolved configuration (ports, hosts,
`DATABASE_URL`) without starting anything, run the same command with
`config` instead of `up -d --build`.

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

After regenerating, rebuild the image (`make up-build`) so the
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
  make test
  ```
  Tests always run inside the `api` container, not on the host — see
  [TESTING.md](TESTING.md). The container must already be up (`make up-build` from step 3).

## Troubleshooting

| Symptom                                                                | Likely Cause                                                                                           | Fix                                                                                                                  |
|------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------|
| `api` container exits immediately                                      | Missing/incorrect `.env` values                                                                        | Check `make logs` and verify `.env` against `.env.example`                                                           |
| `pip install` fails building `mariadb` package                         | Missing MariaDB Connector/C dev headers                                                                | Install `libmariadb-dev` (or platform equivalent) before `pip install`                                               |
| API can't reach the database                                           | Wrong `DB_HOST` for your setup                                                                         | Use `DB_HOST=kws_station_db` for Docker, `DB_HOST=localhost` (or your DB host) for native runs                       |
| `Database did not become reachable in time` after changing the DB port | `DB_PORT` was set to the host port (e.g. `3310`); MariaDB still listens on `3306` inside the container | Keep `DB_PORT=3306` and set the host-side port with `DB_HOST_PORT`; then recreate the stack (`make down && make up`) |
| Changed `DB_HOST` in `.env` but the container still uses the old host  | A hardcoded `DB_HOST` in the `environment:` block overrides `env_file`                                 | Use `DB_HOST: ${DB_HOST:-kws_station_db}` in compose files, not a literal value                                      |
| `alembic upgrade head` fails to connect                                | Database not ready yet                                                                                 | Wait for the `db` container healthcheck to pass, or start the DB first in native setups                              |
