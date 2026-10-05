
# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                          Station AI — Makefile                               ║
# ║  Groups: API · Alembic                                                       ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

.PHONY: \
  migrate migrate-up-index migrate-down-index migrate-up migrate-down \
  build up up-build down restart logs ps \
  _ensure_uv deps-update deps-update-package deps-outdated \
  test test-smoke test-verbose test-cov test-cov-html test-file

# ───────────────────────────────────────────────────────────────────────────
# Everything below (deps-*, test*, migrate-*) runs INSIDE the `api`
# container via `docker compose exec`, not against a local .venv.
#
# The container is the single source of truth for the environment and
# code that actually ships — running these on the host instead would
# risk a drifted local Python (missing pip/uv, wrong version, etc.)
# giving a false pass/fail, or editing requirements.txt against the
# wrong interpreter. The project directory is bind-mounted into the
# container (`volumes: .:/app` in docker-compose.yml), so any file the
# container writes (requirements.txt, migration scripts, coverage
# reports) lands directly on the host, same as if it ran locally.
#
# All targets below require the `api` container to be running first
# (`make up` / `make up-build`).
# ───────────────────────────────────────────────────────────────────────────
# NOTE: intentionally NOT named COMPOSE_FILE — that name collides with
# Docker Compose's own environment variable of the same name.
# --project-directory . makes Compose resolve relative paths (volumes,
# env_file, and its own .env lookup for ${VAR} substitution) against the
# repo root, even though the compose file itself lives in docker/api/.
DC := docker compose -f docker/api/docker-compose.yml --project-directory .

# ───────────────────────────────────────────────────────────────────────────
# Docker — build & run
# ───────────────────────────────────────────────────────────────────────────
## Build (or rebuild) the api image
build:
	$(DC) build
## Start all services in the background
up:
	$(DC) up -d
## Rebuild the api image and start all services in the background
up-build:
	$(DC) up -d --build
## Stop and remove all services
down:
	$(DC) down
## Restart all services (without rebuilding)
restart:
	$(DC) restart
## Tail logs from all services
logs:
	$(DC) logs -f
## Show status of the stack's containers
ps:
	$(DC) ps

# ───────────────────────────────────────────────────────────────────────────
# Dependencies — keep requirements.txt in sync with pyproject.toml
#
# `uv` is required to compile requirements.txt, but it is a developer
# TOOL, not an application dependency — it must NOT be added to
# pyproject.toml's `dependencies`. Instead, each target below ensures
# `uv` is available *inside the api container* (installed on first use)
# before calling it — see docs/INSTALL.md "Dependency Tooling" for the
# manual install command if you prefer to run `uv` yourself.
# ───────────────────────────────────────────────────────────────────────────
_ensure_uv:
	@$(DC) exec api python -m uv --version >/dev/null 2>&1 || $(DC) exec api python -m pip install -q uv

## Recompile requirements.txt with the latest versions allowed by pyproject.toml
deps-update: _ensure_uv
	$(DC) exec api python -m uv pip compile --upgrade pyproject.toml --output-file requirements.txt
## Upgrade a single package only (usage: make deps-update-package package="fastapi")
deps-update-package: _ensure_uv
	$(DC) exec api python -m uv pip compile --upgrade-package $(package) pyproject.toml --output-file requirements.txt
## List installed packages that have newer versions available
deps-outdated:
	$(DC) exec api python -m pip list --outdated

# ───────────────────────────────────────────────────────────────────────────
# Testing — pytest + coverage, run INSIDE the api container (see docs/TESTING.md)
#
# Tests exercise the environment and code as they actually run in the
# container built from docker/api/Dockerfile — not a local .venv, which
# can drift from what's pinned in requirements.txt. There is intentionally
# no local/.venv-based test target: the container IS the thing under
# test. Requires the `api` container to be running (`make up`/`make
# up-build` first). Still uses the isolated in-memory SQLite from
# tests/conftest.py, NOT the `db` MariaDB service — safe to run against
# a live stack without touching real data.
# ───────────────────────────────────────────────────────────────────────────
## Run the smoke checks first, then the full test suite inside the api container
test: test-smoke
	$(DC) exec api python -m pytest -q
## Run only the smoke checks (tests/smoke/*.sh) against the live stack: DB wiring and connectivity.
## They are read-only (SELECT 1 / TCP connect), but unlike pytest they DO talk to the real `db` service.
## DC is passed down so the scripts use the same compose command as the other targets.
test-smoke:
	DC="$(DC)" bash tests/smoke/database_url_check.sh
	DC="$(DC)" bash tests/smoke/db_host_port_check.sh
## Run the full test suite inside the api container with verbose per-test output
test-verbose:
	$(DC) exec api python -m pytest -v
## Run the full test suite inside the api container with a coverage summary (fails if coverage < 80%)
test-cov:
	$(DC) exec api python -m pytest --cov=. --cov-report=term-missing --cov-fail-under=80
## Run tests inside the api container with coverage and generate an HTML report (see htmlcov/index.html inside the container)
test-cov-html:
	$(DC) exec api python -m pytest --cov=. --cov-report=html --cov-report=term-missing
## Run a single test file or node id inside the api container (usage: make test-file file="tests/test_stations.py")
## or make test-file file="tests/test_stations.py::test_create_station_success"
test-file:
	$(DC) exec api python -m pytest -v $(file)

# ───────────────────────────────────────────────────────────────────────────
# Alembic — migration, run INSIDE the api container
# ───────────────────────────────────────────────────────────────────────────
## Autogenerate a new migration revision (usage: make migrate msg="describe the schema change")
migrate:
	$(DC) exec api python -m alembic revision --autogenerate -m "$(msg)"
## Upgrade migration by index (usage: make migrate-up-index index="1")
migrate-up-index:
	$(DC) exec api python -m alembic upgrade $(index)
## Downgrade migration by index (usage: make migrate-down-index index="-1")
migrate-down-index:
	$(DC) exec api python -m alembic downgrade $(index)
## Upgrade all migration
migrate-up:
	$(DC) exec api python -m alembic upgrade head
## Downgrade all migration
migrate-down:
	$(DC) exec api python -m alembic downgrade base

