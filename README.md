# KWS Station API

A FastAPI-based backend service for managing fuel/charging stations, customers,
and related services. Uses SQLAlchemy + Alembic on top of MariaDB.

## Tech Stack

- **Language:** Python 3.14
- **Framework:** FastAPI (served via Uvicorn)
- **Database:** MariaDB (via the `mariadb` connector / SQLAlchemy)
- **Migrations:** Alembic
- **Auth:** JWT (PyJWT) + `fastapi-login`, password hashing via `bcrypt`
- **Containerization:** Docker & Docker Compose

## Documentation

| Doc                                              | Covers                                               |
|--------------------------------------------------|------------------------------------------------------|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)     | Request flow, layering, module responsibilities      |
| [docs/DATABASE.md](docs/DATABASE.md)             | Schema, tables, migrations                           |
| [docs/AUTHENTICATION.md](docs/AUTHENTICATION.md) | JWT + cookie + DB-backed session design              |
| [docs/API.md](docs/API.md)                       | Endpoint reference                                   |
| [docs/TESTING.md](docs/TESTING.md)               | How the test suite works, coverage, adding tests     |
| [docs/ISSUES.md](docs/ISSUES.md)                 | Known issues, security findings, improvement backlog |
| [docs/INSTALL.md](docs/INSTALL.md)               | Full installation guide (Docker & native)            |

## Project Structure

```
kws_station_api/
├── alembic/            # Database migrations
├── auth/               # Authentication (JWT, password hashing, dependencies)
├── database/           # SQLAlchemy engine & session setup
├── models/             # SQLAlchemy ORM models
├── routers/            # FastAPI route handlers (auth, customer, service, stations)
├── scripts/            # One-off/utility scripts (create_user, fake_stations)
├── tests/              # Test suite
├── validations/        # Pydantic request/response schemas
├── config/             # Centralized application configuration (Config dataclass)
├── exceptions/         # Shared HTTPException instances reused across routers
├── main.py             # FastAPI application entrypoint
├── docker/
│   └── api/            # API container stack (extend with docker/<service>/ as needed)
│       ├── Dockerfile
│       ├── docker-compose.yml       # API + MariaDB stack (local development)
│       ├── docker-compose.prod.yml  # Production override (joins kws_default network)
│       ├── docker-compose.ci.yml    # Standalone CI stack (separate names/ports)
│       └── entrypoint.sh            # Waits for DB, runs migrations, starts Uvicorn
├── docs/               # Architecture, database, auth, API, testing, issues docs
├── renovate.json        # Automated dependency update bot config
└── Makefile             # Common dev/ops commands
```

## Requirements

- Python 3.14+
- MariaDB (local install) **or** Docker + Docker Compose (recommended)

## Quick Start (Docker — recommended)

See [docs/INSTALL.md](docs/INSTALL.md) for the full installation guide.

```bash
cp .env.example .env   # fill in real secrets
make up-build          # build images and start the stack
```

Database migrations are applied **automatically** on container startup (see
`docker/api/entrypoint.sh`) — no separate `make migrate-up` step is needed
when running via Docker.

> **Database ports:** keep `DB_PORT=3306` (the port MariaDB listens on
> *inside* the Docker network, used by the API). To change the port exposed
> on your machine, set `DB_HOST_PORT` (default `3310`) instead. See
> [docs/INSTALL.md](docs/INSTALL.md#2-configure-environment-variables).

The API will be available at `http://localhost:${APP_PORT}` (default `8000`,
unless overridden in `.env`).

## Local Development (without Docker)

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn main:app --reload
```

## Keeping Dependencies Up to Date

`pyproject.toml` lists only **direct** dependencies (packages actually
imported by application code) using compatible-release ranges (`>=current,<next-major>`) — e.g.
`fastapi>=0.142.2,<1.0.0`. This lets
patch/minor releases be picked up automatically; a library's own
major-version bump still requires a deliberate, tested decision (raise
the upper bound by hand after verifying the suite passes).

`requirements.txt` is the fully-pinned (`==`), reproducible lockfile
compiled *from* `pyproject.toml` — it also pins every transitive
dependency (not declared by hand). To refresh it:

`make deps-update*`/`deps-outdated` run inside the `api` container (requires it running — `make up`/`make up-build`
first):

```bash
make deps-update                        # recompile requirements.txt (all packages), then install it in the container
make deps-update-package package="fastapi"   # same, but upgrade a single package
make deps-outdated                       # list packages with newer versions available
```

Both `deps-update*` targets run `uv pip compile` first and, only if it
succeeds, `uv pip install --system -r requirements.txt` in the running
container. Rebuild the image (`make up-build`) to make the change permanent.

After running `make deps-update`, always run `make test-cov` before
committing — if a minor/patch bump breaks something, pin that one
package back down in `pyproject.toml` and document why in
[docs/ISSUES.md](docs/ISSUES.md) (see the "Dependency Audit" section for
an example of this workflow).

Automated update PRs can also be produced by [Renovate](https://docs.renovatebot.com/)
using the included [`renovate.json`](renovate.json), if a Renovate bot/runner
is configured against this repository.

## Testing

```bash
make up-build    # build & start the stack first, if not already running

make test        # smoke checks first, then the full pytest suite inside the api container
make test-smoke  # only the smoke checks (DB wiring/connectivity, needs bash)
make test-cov    # pytest with coverage summary (fails if < 80%)
```

The pytest suite always runs inside the `api` container (against an
isolated in-memory SQLite, not the real `db`) — there is no local/host-based
test target. The smoke checks (`tests/smoke/`) are the exception: they run
through `bash` on the host, call `docker compose exec`, and talk to the real
`db` (read-only). `make test` stops before pytest if a smoke check fails.
See [docs/TESTING.md](docs/TESTING.md) for details.

See [docs/TESTING.md](docs/TESTING.md) for the full breakdown of what's
covered and how fixtures work.

## Known Issues & Backlog

See [docs/ISSUES.md](docs/ISSUES.md) for security findings, correctness
bugs, and an improvement backlog — including bugs found and fixed while
building the test suite.

## Available Make Commands

| Command                                | Description                                                                          |
|----------------------------------------|--------------------------------------------------------------------------------------|
| `make build`                           | Build (or rebuild) the API image                                                     |
| `make up`                              | Start all services in the background                                                 |
| `make up-build`                        | Rebuild the API image and start all services                                         |
| `make down`                            | Stop and remove all services                                                         |
| `make restart`                         | Restart all services without rebuilding                                              |
| `make logs`                            | Tail logs from all services                                                          |
| `make ps`                              | Show status of the stack's containers                                                |
| `make migrate msg="..."`               | Autogenerate a new migration revision                                                |
| `make migrate-up`                      | Apply all pending migrations                                                         |
| `make deps-update`                     | Recompile `requirements.txt` from `pyproject.toml`, then install it in the container |
| `make deps-update-package package="x"` | Upgrade a single package only, then install `requirements.txt` in the container      |
| `make deps-outdated`                   | List installed packages with newer versions                                          |
| `make migrate-down`                    | Revert all migrations                                                                |
| `make migrate-up-index index="1"`      | Apply a specific migration                                                           |
| `make migrate-down-index index="1"`    | Revert a specific migration                                                          |

For testing commands (`make test`, `make test-smoke`, `make test-verbose`,
`make test-cov`, `make test-cov-html`, `make test-file`), see
[docs/TESTING.md](docs/TESTING.md).

## Configuration

All configuration is driven by environment variables — see
[`.env.example`](.env.example) for the full list and
[docs/INSTALL.md](docs/INSTALL.md) for details on each variable.

## API Documentation

Once the service is running, interactive API docs (Swagger UI) are available at:

```
http://localhost:${APP_PORT}/docs
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on contributing to this project.

## License

This project is licensed under the terms described in [LICENSE](LICENSE).
