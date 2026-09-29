
# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                          Station AI — Makefile                           ║
# ║  Groups: API · Alembic  ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

.PHONY: \
  migrate-up-index migrate-down-index migrate-up migrate-down
# ──────────────────────────────────────────────────────────────────────────────
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
