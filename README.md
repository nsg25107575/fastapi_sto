# KWS Station API

A FastAPI-based backend service for managing fuel/charging stations, customers,
and related services. Uses SQLAlchemy + Alembic on top of MariaDB.

## Tech Stack

- **Language:** Python 3.14
- **Framework:** FastAPI (served via Uvicorn)
- **Database:** MariaDB (via the `mariadb` connector / SQLAlchemy)
- **Migrations:** Alembic
- **Auth:** JWT (PyJWT) + `fastapi-login`, password hashing via `argon2-cffi` / `passlib`
- **Containerization:** Docker & Docker Compose

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
├── validation/         # Pydantic request/response schemas
├── config.py           # Centralized application configuration
├── main.py             # FastAPI application entrypoint
├── docker/
│   └── api/            # API container stack (extend with docker/<service>/ as needed)
│       ├── Dockerfile
│       ├── docker-compose.yml   # API + MariaDB stack
│       └── entrypoint.sh        # Waits for DB, runs migrations, starts Uvicorn
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
make docker-up-build   # build images and start the stack
make migrate-up        # apply database migrations
```

Database migrations are applied **automatically** on container startup (see
`docker/api/entrypoint.sh`) — no separate `make migrate-up` step is needed
when running via Docker.

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

`requirements.txt` is a pinned, compiled lockfile generated from
`pyproject.toml`. To refresh it:

```bash
make deps-update                        # upgrade everything within pyproject.toml constraints
make deps-update-package package="fastapi"   # upgrade a single package
make deps-outdated                       # list packages with newer versions available
```

Automated update PRs can also be produced by [Renovate](https://docs.renovatebot.com/)
using the included [`renovate.json`](renovate.json), if a Renovate bot/runner
is configured against this repository.

## Available Make Commands

| Command                             | Description                                  |
|-------------------------------------|----------------------------------------------|
| `make docker-build`                 | Build (or rebuild) the API image             |
| `make docker-up`                    | Start all services in the background         |
| `make docker-up-build`              | Rebuild the API image and start all services |
| `make docker-down`                  | Stop and remove all services                 |
| `make docker-restart`               | Restart all services without rebuilding      |
| `make docker-logs`                  | Tail logs from all services                  |
| `make docker-ps`                    | Show status of the stack's containers        |
| `make migrate-up`                   | Apply all pending migrations                 |
| `make deps-update`                   | Recompile `requirements.txt` from `pyproject.toml` |
| `make deps-update-package package="x"` | Upgrade a single package only            |
| `make deps-outdated`                 | List installed packages with newer versions |
| `make migrate-down`                 | Revert all migrations                        |
| `make migrate-up-index index="1"`   | Apply a specific migration                   |
| `make migrate-down-index index="1"` | Revert a specific migration                  |

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
