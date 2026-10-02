# Contributing to KWS Station API

Thank you for your interest in contributing. This document describes the
expected workflow and code standards for this project.

## Getting Started

1. Fork/clone the repository.
2. Follow the installation steps in [docs/INSTALL.md](docs/INSTALL.md) to get
   a working local environment (Docker or native Python).
3. Create a feature branch from `main`:
   ```bash
   git checkout -b feature/short-description
   ```

## Development Workflow

1. **Write/update tests first** where practical (unit or integration) for the
   behavior you are changing.
2. **Implement the change.**
3. **Run the test suite** (inside the `api` container — see
   [docs/TESTING.md](docs/TESTING.md)) and make sure it passes:
   ```bash
   make up-build   # if the container isn't already running
   make test
   ```
4. **Run database migrations** if your change touches the schema:
   (also run inside the `api` container — see [docs/DATABASE.md](docs/DATABASE.md))
   ```bash
   # Create a new revision
   make migrate-revision msg="describe your change"
   # Apply it
   make migrate-up
   ```
5. **Update documentation** (`README.md`, `docs/INSTALL.md`, or inline
   docstrings) if your change affects setup, configuration, or public
   behavior.

## Code Standards

- Target **Python 3.14**.
- Follow **PEP 8** style conventions.
- Use **type hints** for function signatures and dataclass fields.
- Keep comments and docstrings **in English**.
- Prefer explicit, descriptive names over abbreviations.
- Keep route handlers thin — put business logic in dedicated modules
  (models/services) rather than directly in `routers/`.
- Validate all request/response payloads with Pydantic schemas under
  `validations`.

## Environment Variables

- Never commit real secrets. `.env` is git-ignored — only `.env.example`
  (with placeholder values) should be committed.
- When adding a new environment variable:
  1. Add it to `.env.example` with a safe placeholder/default.
  2. Document it in [docs/INSTALL.md](docs/INSTALL.md).
  3. Read it via `config/config.py` (`Config` dataclass) rather than calling
     `os.getenv()` directly elsewhere in the codebase.

## Database Migrations

- All schema changes must go through Alembic — do not modify the database
  schema manually.
- One logical change per migration; give migrations descriptive messages.
- Migrations must be reversible (implement both `upgrade()` and
  `downgrade()`) whenever feasible.

## Docker

All Docker assets live under `docker/api/` (not the project root) — see
`docker/api/Dockerfile`, `docker/api/docker-compose.yml`, and
`docker/api/entrypoint.sh`. The entrypoint applies Alembic migrations
automatically on container start, so no manual migration step is needed
when testing changes via Docker.

- If you change dependencies (`requirements.txt`/`pyproject.toml`) or system
  packages needed to build the image, update `docker/api/Dockerfile`
  accordingly and verify the image still builds:
  ```bash
  make build
  ```
- Prefer regenerating `requirements.txt` via `make deps-update` (or
  `make deps-update-package package="x"` for a single package) rather than
  hand-editing it — see [docs/INSTALL.md](docs/INSTALL.md#5-keeping-dependencies-up-to-date).
- If you add a new required environment variable that the container needs,
  update `docker/api/docker-compose.yml`, `.env.example`, and
  [docs/INSTALL.md](docs/INSTALL.md) together.
- If you need to add another service to the stack (e.g. a worker or nginx),
  create a new `docker/<service>/` directory following the same pattern as
  `docker/api/`.

## Submitting Changes

1. Make sure `make test` passes and the Docker image builds cleanly.
2. Keep commits focused and messages descriptive.
3. Open a pull request describing:
   - What changed and why.
   - Any new environment variables or migrations introduced.
   - How you tested the change.

## Reporting Issues

When reporting a bug, please include:
- Steps to reproduce.
- Expected vs. actual behavior.
- Relevant logs (`make logs`) and environment details (Python
  version, Docker version, OS).
