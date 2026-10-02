
# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                          Station AI — Makefile                               ║
# ║  Groups: API · Alembic                                                       ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

.PHONY: \
  migrate-up-index migrate-down-index migrate-up migrate-down \
  build up up-build down restart logs ps \
  _ensure_uv deps-update deps-update-package deps-outdated \
  test test-verbose test-cov test-cov-html test-file
# ───────────────────────────────────────────────────────────────────────────
# Docker — build & run
# ───────────────────────────────────────────────────────────────────────────
# NOTE: intentionally NOT named COMPOSE_FILE — that name collides with
# Docker Compose's own environment variable of the same name.
# --project-directory . makes Compose resolve relative paths (volumes,
# env_file, and its own .env lookup for ${VAR} substitution) against the
# repo root, even though the compose file itself lives in docker/api/.
DC := docker compose -f docker/api/docker-compose.yml --project-directory .

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
# pyproject.toml's `dependencies`. Instead, each target below ensures a
# local `uv` is available (installed into the active venv on first use)
# before calling it. See docs/INSTALL.md "Dependency Tooling" for the
# manual install command if you prefer to run `uv` yourself.
# ───────────────────────────────────────────────────────────────────────────
_ensure_uv:
	@python -m uv --version >/dev/null 2>&1 || python -m pip install -q uv

## Recompile requirements.txt with the latest versions allowed by pyproject.toml
deps-update: _ensure_uv
	python -m uv pip compile --upgrade pyproject.toml --output-file requirements.txt
## Upgrade a single package only (usage: make deps-update-package package="fastapi")
deps-update-package: _ensure_uv
	python -m uv pip compile --upgrade-package $(package) pyproject.toml --output-file requirements.txt
## List installed packages that have newer versions available
deps-outdated:
	python -m pip list --outdated

# ───────────────────────────────────────────────────────────────────────────
# Testing — pytest + coverage (see docs/TESTING.md)
# ───────────────────────────────────────────────────────────────────────────
## Run the full test suite (isolated SQLite, no Docker/MariaDB required)
test:
	pytest -q
## Run the full test suite with verbose per-test output
test-verbose:
	pytest -v
## Run the full test suite with a coverage summary (fails if coverage < 80%)
test-cov:
	pytest --cov=. --cov-report=term-missing --cov-fail-under=80
## Run tests with coverage and generate an HTML report (see htmlcov/index.html)
test-cov-html:
	pytest --cov=. --cov-report=html --cov-report=term-missing
## Run a single test file or node id (usage: make test-file file="tests/test_stations.py")
## or make test-file file="tests/test_stations.py::test_create_station_success"
test-file:
	pytest -v $(file)

# ───────────────────────────────────────────────────────────────────────────
# Alembic — migration
# ───────────────────────────────────────────────────────────────────────────
## Upgrade migration by index
## Usage:
##   make migrate upgrade index="1" — upgrade migration ${index}
migrate-up-index:
	alembic upgrade $(index)
## Downgrade migration by index
## Usage:
##   make migrate downgrade index="1" — downgrade migration ${index}
migrate-down-index:
	alembic downgrade $(index)
## Upgrade all migration
migrate-up:
	alembic upgrade head
## Downgrade all migration
migrate-down:
	alembic downgrade base
