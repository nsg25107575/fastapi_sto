
# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                          Station AI — Makefile                               ║
# ║  Groups: API · Alembic                                                       ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

.PHONY: \
  migrate-up-index migrate-down-index migrate-up migrate-down \
  docker-build docker-up docker-up-build docker-down docker-restart docker-logs docker-ps \
  deps-update deps-update-package deps-outdated
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
docker-build:
	$(DC) build
## Start all services in the background
docker-up:
	$(DC) up -d
## Rebuild the api image and start all services in the background
docker-up-build:
	$(DC) up -d --build
## Stop and remove all services
docker-down:
	$(DC) down
## Restart all services (without rebuilding)
docker-restart:
	$(DC) restart
## Tail logs from all services
docker-logs:
	$(DC) logs -f
## Show status of the stack's containers
docker-ps:
	$(DC) ps

# ───────────────────────────────────────────────────────────────────────────
# Dependencies — keep requirements.txt in sync with pyproject.toml
# ───────────────────────────────────────────────────────────────────────────
## Recompile requirements.txt with the latest versions allowed by pyproject.toml
deps-update:
	uv pip compile --upgrade pyproject.toml --output-file requirements.txt
## Upgrade a single package only (usage: make deps-update-package package="fastapi")
deps-update-package:
	uv pip compile --upgrade-package $(package) pyproject.toml --output-file requirements.txt
## List installed packages that have newer versions available
deps-outdated:
	uv pip list --outdated

# ───────────────────────────────────────────────────────────────────────────
# Alembic — migration
# ──────────────────────────────────────────────────────────────────────────────
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
