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

make test            # run the full suite inside the api container
make test-verbose    # same, with per-test output
make test-cov        # run with coverage summary, fails if < 80%
make test-cov-html   # generate an HTML coverage report (inside the container)
make test-file file="tests/test_stations.py"              # single file
make test-file file="tests/test_stations.py::test_create_station_success"  # single test
```

Each target runs `docker compose exec api python -m pytest ...` under
the hood (see the `Makefile`). Equivalent raw command (if not using
`make`):

```bash
docker compose -f docker/api/docker-compose.yml --project-directory . exec api python -m pytest -q
```

The `api` container itself still needs a valid `.env` and the `db`
service running to start up normally (see [INSTALL.md](INSTALL.md)) —
but once it's up, the test suite never touches that real database:
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

Running `make test`/`make test-cov` produces **zero warnings** on a
clean build. If you see any (e.g. `PydanticDeprecatedSince20`,
`StarletteDeprecationWarning`, `InsecureKeyLengthWarning`), fix the root
cause rather than suppressing — see [ISSUES.md](ISSUES.md) for examples.

## Test Layout

| File                                             | Scope                                                                                                                                        |
|--------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------|
| `tests/conftest.py`                              | Shared fixtures: `client` (TestClient wired to SQLite), `db_session` (raw session), `user_factory`, `auth_client` (pre-authenticated client) |
| `../tests/auth/test_auth_password.py`            | Unit — `auth/password.py` bcrypt hashing/verification                                                                                        |
| `tests/test_validation_user.py`                  | Unit — `validations/user.py` password-strength & name validators                                                                             |
| `../tests/routers/test_auth_router.py`           | Integration — `/auth/sign-up`, `/sign-in`, `/sign-out`, `/me`                                                                                |
| `../tests/station/test_stations.py`              | Integration — `/stations/*` CRUD + nearest search                                                                                            |
| `../tests/services/test_services_router.py`      | Integration — `/services/*` CRUD                                                                                                             |
| `tests/test_customer_router.py`                  | Integration — `POST /customer`                                                                                                               |
| `../tests/station/test_station_model.py`         | Unit — `StationModel` classmethods (soft delete, restore, nearest search)                                                                    |
| `../tests/station/test_station_service_model.py` | Unit — `StationServiceModel` classmethods                                                                                                    |
| `../tests/station/test_station_user_model.py`    | Unit — `StationUserModel` (role assignment, unique constraint)                                                                               |
| `../tests/user/test_user_model.py`               | Unit — `UserModel.get_user_by_email`                                                                                                         |

## Why `database.engine` Is Monkey-Patched in `conftest.py`

Most routers accept a `Session = Depends(get_session)`, which FastAPI's
`app.dependency_overrides` can swap for the test session cleanly. However,
`routers/auth.py` opens its own session directly via
`with Session(engine) as session:`, importing the module-level `engine`
from `database.engine` — bypassing the dependency-injection override
entirely.

To keep auth endpoints testable without changing production code's
calling convention, `tests/conftest.py` replaces
`database.engine.engine` and `database.engine.SessionLocal` with the
test engine **before** importing `main` (which transitively imports every
router). This is a pragmatic workaround — the real fix is tracked as
ISSUE-18 in [ISSUES.md](ISSUES.md): routers should consistently receive
their session via the `get_session` dependency rather than importing the
global engine directly.

## Coverage

Current baseline (application code only, excluding `tests/`, `alembic/`,
`scripts/`, `main.py`'s `if __name__` entrypoint — see `.coveragerc`):
**~96%**, well above the 80% target.

Known coverage gaps (intentional, documented, not pursued further):

- `StationModel.search_stations_by_name`'s `MATCH()/AGAINST()` query path (MariaDB-only — see Philosophy above).
- A couple of defensive branches in `database/engine.py` (the non-SQLite
  pool-kwargs branch, exercised implicitly by every non-test run but not
  by the SQLite-based suite itself) and `main.py`'s manual
  `uvicorn.run(...)` entrypoint block.

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
