# Testing

## Philosophy

Tests run **inside the `api` container**, not against a local `.venv` —
the container is built from `docker/api/Dockerfile` and
`requirements.txt`, so it's the exact environment and code that actually
ships. There is intentionally no local/host-based way to run the suite:
testing the container is testing the real thing, with no risk of a
drifted local Python install (missing `pip`/`uv`, wrong Python version,
accidentally-uninstalled packages) giving a false pass or fail.

The suite runs against an **in-memory SQLite database**, not the real
MariaDB — this makes tests fast and hermetic, and means they can run
against a live stack without ever touching real data. Every test
function gets a freshly created/dropped schema (`tests/conftest.py`,
`_fresh_schema` autouse fixture), so tests are fully isolated from each
other.

SQLite is sufficient for everything exercised here: SQLAlchemy ORM CRUD,
relationships, soft-delete filtering, and even the plain SQL math
functions used by `StationModel.read_nearest_stations`
(`acos`/`radians`/`cos`/`sin` — all natively supported). The one exception
is `StationModel.search_stations_by_name`, which relies on MariaDB's
`FULLTEXT` index and `MATCH() ... AGAINST()` syntax — SQLite has no
equivalent. That method's query-building guard clause (rejecting queries
under 3 characters) is tested directly; the full-text search path itself
is documented as **requiring manual/integration testing against a real
MariaDB instance** (see `test_search_stations_by_name_full_text_requires_mariadb`
in `../tests/station/test_station_model.py`).

## Running Tests

The `api` container must be running first (`make up` or `make
up-build`):

```bash
make up-build        # build & start the stack, if not already running

make test            # smoke checks first (make test-smoke), then the full pytest suite
make test-smoke      # only the smoke checks (DB wiring/connectivity, see below)
make test-verbose    # same, with per-test output
make test-cov        # run with coverage summary, fails if < 80%
make test-cov-html   # generate an HTML coverage report (inside the container)
make test-file file="tests/station/test_stations.py"      # single file
make test-file file="tests/station/test_stations.py::test_create_station_success"  # single test
```

Each pytest target runs `docker compose exec api python -m pytest ...` under
the hood (see the `Makefile`). Equivalent raw command (if not using
`make`):

```bash
docker compose -f docker/api/docker-compose.yml --project-directory . exec api python -m pytest -q
```

`make test` runs the smoke checks **before** pytest and stops on the first
failure, so a mis-wired stack is reported immediately instead of as a wall
of unrelated test errors. Only `make test` includes them; the other `test-*`
targets run pytest alone.

### Smoke Checks (`tests/smoke/`)

Shell scripts that verify the **running stack** is wired correctly. Unlike
pytest (isolated in-memory SQLite), they talk to the real `db` service, but
are read-only (`SELECT 1` and a TCP connect) and never print credentials.

| Script                              | Verifies                                                                                                                                               |
|-------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|
| `tests/smoke/database_url_check.sh` | `DATABASE_URL` has the `user:password@host:port/db` shape and the app can authenticate and run `SELECT 1`                                              |
| `tests/smoke/db_host_port_check.sh` | `DATABASE_URL` host/port match `DB_HOST`/`DB_PORT` (what `entrypoint.sh` waits on), and `DB_HOST:DB_PORT` is reachable from inside the `api` container |

The second script guards against mixing up `DB_PORT` (port inside the Docker
network, `3306`) with `DB_HOST_PORT` (port published on the host), and
against a hardcoded `DB_HOST` in a compose file diverging from
`DATABASE_URL`. Run them on their own with `make test-smoke`. Both scripts
are executed via `bash`, so the executable bit is not required.

`db_host_port_check.sh` accepts a `DC` variable to target another compose
stack (e.g. the CI one); `database_url_check.sh` is currently fixed to
`docker/api/docker-compose.yml`.

The `api` container itself still needs a valid `.env` and the `db`
service running to start up normally (see [INSTALL.md](INSTALL.md)) —
but once it's up, the pytest suite never touches that real database:
`tests/conftest.py` forces `DATABASE_URL=sqlite:///:memory:` (and dummy
JWT/cookie secrets) before anything else is imported.

> **Note on container env vars:** `conftest.py` *forcibly overwrites*
> `DATABASE_URL`, `JWT_SECRET_KEY`, `COOKIES_SECRET_KEY`, and
> `COOKIES_SECURE` (not `os.environ.setdefault`) specifically because the
> `api` container's `docker-compose.yml` already injects real values for
> these as OS-level environment variables before Python even starts.
> Using `setdefault` there would silently keep `COOKIES_SECURE=True`,
> which breaks the `station` cookie round-trip over `TestClient`'s plain
> HTTP requests and makes every authenticated test fail with 401 — this
> was a real bug caught by actually running tests inside the container.

The latest full run (Python 3.14.10 in the API container) completed with **278 passed** and **four deprecation
warnings**: two from SlowAPI calling
`asyncio.iscoroutinefunction`, and two from Starlette's `TestClient` when
tests pass per-request cookies. These originate in dependency code; do not
silence them globally. Recheck after dependency upgrades.

## Test Layout

| Path                                                     | Scope                                                                                   |
|----------------------------------------------------------|-----------------------------------------------------------------------------------------|
| `tests/auth/`, `tests/routers/`                          | Password and authorization unit tests; auth endpoints, rate limits, and docs access     |
| `tests/station/`                                         | Station, service, station-user model tests and station/contact HTTP endpoints           |
| `tests/orders/`, `tests/reviews/`, `tests/chat/`         | Order model and HTTP tests, review model tests, chat model tests                        |
| `tests/services/`                                        | Service HTTP tests and email service tests                                              |
| `tests/i18n/`, `tests/validations/`, `tests/exceptions/` | Translation, validation, and exception behavior                                         |
| `tests/test_*.py`                                        | Configuration, customer/geocoding/pagination, seeders, docs access, and user validation |
| `tests/smoke/`                                           | Shell checks for live-stack database configuration and connectivity                     |

## Why `database.engine` Is Monkey-Patched in `conftest.py`

Most routes receive a `Session = Depends(get_session)`, which FastAPI's
`app.dependency_overrides` replaces with the SQLite test session. The
`load_user` callback in `auth/dependencies.py` is an exception: it opens
`Session(engine)` directly to resolve a token to a user, bypassing that
override.

`tests/conftest.py` therefore replaces `database.engine.engine` and
`database.engine.SessionLocal` before importing `main`, while also
overriding `get_session` for request dependencies. This keeps token lookup
on the isolated SQLite database. The dependency's direct engine access is
the remaining exception to the normal session-injection pattern.

## Coverage

The latest full `pytest --cov=. --cov-report=term-missing --cov-fail-under=80`
run collected **278 tests**, all passing, and measured **90.2% statement
coverage** (1,602 statements; 157 missed). Coverage excludes `tests/`,
`.venv/`, `alembic/`, `scripts/`, and `main.py`, as configured in
[`.coveragerc`](../.coveragerc). The Makefile enforces an 80% minimum.

Notable gaps from that run:

- `routers/chat.py`: **41.0%**; tests currently cover chat models, not the
  message endpoints and their customer-cookie/room-ownership checks.
- `routers/review.py`: **72.7%**; the review model is tested, but the HTTP
  endpoint is not.
- `routers/stations.py`: **79.8%**; the admin moderation endpoint is not
  covered.
- `routers/order.py`: **89.6%**; the unknown `customer_device` cookie path
  is untested and currently calls an unimported exception; see
  [ISSUE-19](ISSUES.md#correctness--consistency).
- `seeders/__main__.py` and `seeders/create.py`: **0%**; command-line entry
  points are not exercised.
- `StationModel.search_stations_by_name` uses MariaDB `FULLTEXT` and
  `MATCH() ... AGAINST()`; its database-specific query path needs a MariaDB
  integration test. The SQLite suite covers the short-query guard only.
- `database/engine.py`'s non-SQLite pool configuration and the application
  entrypoint are not exercised by this suite.

## Adding New Tests

- Prefer **unit tests** (direct model/validator calls via `db_session`)
  for business logic, and **integration tests** (via `client`/`auth_client`)
  for HTTP-contract behavior (status codes, response shapes, auth gating).
- Use the `auth_client` fixture for anything requiring authentication —
  it signs up a fresh user and returns `(client, user_payload)`.
- Each test must be independent — do not rely on data created by another
  test; the schema is recreated per-test.
- If you add a model, consider whether it needs its own
  `test_<model>_model.py` file for classmethod coverage, separate from any
  router-level integration tests.
