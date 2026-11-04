# Issues & Improvement Backlog

Current open items and resolved findings from codebase reviews, updated
2026-11-04. Resolved entries are retained as implementation history.
Priority: 🔴 High (security or correctness bug) · 🟡 Medium (robustness/consistency) · 🟢 Low (polish).

## Security

### ✅ ISSUE-1 (RESOLVED): Production accepts the default JWT secret

`JWT_SECRET_KEY` still has a development fallback, but startup now raises
when `APP_ENV=production` and that default is in use. The cookie uses the
JWT signing key; `COOKIES_SECRET_KEY` is not currently read by the app.

### ✅ ISSUE-2 (RESOLVED): Station ownership not enforced on update/delete

`PUT /stations/{id}` and `DELETE /stations/{id}` now call
`check_station_ownership` and return `403` for non-owners. Station employee
permissions are handled separately by the shared authorization layer.

### 🟡 ISSUE-3: `COOKIES_SECRET_KEY` is unused

`COOKIES_SECRET_KEY` is not loaded by `Config` or passed to
`fastapi-login`; the JWT signing key secures the session cookie. Remove the
unused setting or wire it into a separate cookie-signing mechanism.

### ✅ ISSUE-4 (RESOLVED): No rate limiting on auth endpoints

`/auth/sign-in` and `/auth/sign-up` are limited to five requests per minute
using SlowAPI.

### 🟡 ISSUE-5: `request.client.host` unreliable behind a proxy
`routers/customer.py` uses `request.client.host` directly as the stored
`ip`, which returns the reverse proxy's IP in production, not the real
client.
**Fix:** honor `X-Forwarded-For` (first hop) when present, falling back to
`request.client.host`.

### 🟢 ISSUE-6: Session tokens never cleaned up
`tokens` rows are only deleted on explicit sign-out; expired-but-unused
rows accumulate forever.
**Fix:** add a periodic cleanup (cron/scheduled task or a `DELETE WHERE
expires_at < NOW()` run via Alembic-adjacent maintenance script).

## Correctness / Consistency

### ✅ ISSUE-7 (RESOLVED): Mixed request styles in the services router

The services router now uses `ServiceCreateSchema` and
`ServiceUpdateSchema` JSON request bodies.

### ✅ ISSUE-8 (RESOLVED): Mixed-language error messages

Service-not-found messages now use the i18n layer with `en`, `uk`, and `pl`
translations; the hardcoded Russian message was removed.

### ✅ ISSUE-9 (RESOLVED): Inconsistent auth success/error envelopes

Authentication success responses and application HTTP/validation errors now
use the shared `APIResponse` shape. Other successful resource endpoints
continue to return their resource schema directly.

### ✅ ISSUE-10 (RESOLVED): User soft-delete behavior missing

`UserModel` now uses `SoftDeleteMixin`, so deleted users are hidden from
default queries and authentication lookups.

### ✅ ISSUE-11 (RESOLVED): `station_id` not validated in services router

`POST /services/` now checks that the station exists before creating a
service and returns the station-not-found response otherwise.

### ✅ ISSUE-12 (RESOLVED): Confusing auth handler name

The current-user endpoint handler is named `get_me`, distinct from the
authentication dependency.

### 🟡 ISSUE-18: `load_user` bypasses session dependency injection

Most routes use `Depends(get_session)`, but the `load_user` callback in
`auth/dependencies.py` opens `Session(engine)` directly. Tests must patch the
shared engine before importing the app in addition to overriding the request
dependency (see [TESTING.md](TESTING.md)). Consider injecting the session
consistently if the authentication library integration permits it.

### 🟡 ISSUE-19: Unknown customer cookie can raise `NameError` when reading an order

In `routers/order.py`, the branch for a non-empty `customer_device` cookie
that does not match a customer calls
`customer_not_found_unauthorized_exception()`, but that exception is not
imported into the module. The request therefore raises `NameError` instead
of returning the intended unauthorized response. Add the missing import and
a router test for an unknown customer cookie.

### 🟡 ISSUE-20: `COOKIES_SECURE=False` is interpreted as true

`config/config.py` sets `cookie_secure` with `bool(os.getenv(...))`.
Environment values are strings, so any non-empty value—including the
documented `.env.example` value `False`—enables the `Secure` cookie flag.
Parse accepted boolean strings explicitly and test both true and false
values.

### 🟡 ISSUE-21: `JWT_EXPIRES_IN` is not used for token expiry

`Config.jwt_expires_in` reads `JWT_EXPIRES_IN`, but `auth/config.py`
configures `LoginManager.default_expiry` from
`MAX_COOKIE_AGE_IN_DAYS` instead. Either wire the seconds-based setting into
token creation or remove/document the unused setting consistently.

## Dependency Hygiene

### ✅ ISSUE-13 (RESOLVED 2026-10-02): Redundant password-hashing libraries

`passlib`, `pwdlib`, and `argon2-cffi` were removed from
`pyproject.toml`/`requirements.txt`; `auth/password.py` uses `bcrypt`
directly. See the [dependency audit](#dependency-audit--update-2026-10-02)
below.

### ✅ ISSUE-14 (RESOLVED 2026-10-02): `services==0.1.1` dependency unclear

The unused generically-named `services` package was removed from the
dependency files.

## Feature Gaps

### 🟢 ISSUE-15: API routes missing for some modeled entities

Station contacts now have CRUD routes, and station employee roles are used
by authorization checks. There are still no standalone routes for
`station_customers`, role/user assignment, `station_work_schedule`,
`vehicles`, or `fuel_types`.

### ✅ ISSUE-16 (RESOLVED): No role/permission enforcement

`auth/authorization.py` now checks station ownership and explicit employee
permissions. For example, the Manager role grants station updates, service
and contact management, and order management; other configured employee
roles have no permissions by default.

### 🟢 ISSUE-17: No email verification or password reset flow

`users.email_verified` exists but is never set, and there is no
forgot-password endpoint. An email service is available; implement the
verification/reset token flows and their API endpoints.

## Documentation Gaps (addressed in this pass)

- ✅ Added `docs/ARCHITECTURE.md`, `docs/DATABASE.md`,
  `docs/AUTHENTICATION.md`, `docs/API.md`, `docs/TESTING.md`.
- ✅ Added this `ISSUES.md` backlog.

## Bugs Found & Fixed During This Pass (2026-10-02)

While building the test suite, the following **real, previously-latent
production bugs** were found (not test-authoring mistakes) and fixed:

1. 🔴 **Auth was completely broken** — `auth/dependencies.py` used
   `@manager.user_loader` instead of `@manager.user_loader()` (missing
   call parentheses on the factory). `fastapi-login`'s `_user_callback`
   was therefore never actually registered, so *every* authenticated
   request would fail with `Exception: Missing user_loader callback`. **This means session-cookie authentication never
   worked in this
   codebase prior to this fix.**
2. 🔴 `StationModel.update_station` / `delete_station` crashed with an
   unhandled `AttributeError` (not a clean 404) when called with a
   nonexistent `station_id`, because neither checked `read_station()`'s
   result for `None` before use.
3. 🔴 `StationModel.restore_station` could never actually restore a
   soft-deleted station — it called `read_station()`, which applies the
   global `deleted_at IS NULL` filter, so a soft-deleted row was always
   invisible to it.
4. 🟡 `routers/auth.py:sign_in` declared `status_code=202` on the route
   but built its `JSONResponse` without an explicit status, so Starlette
   silently returned `200` instead of the documented `202`.
5. 🟡 `POST /customer` required `ip` and `device_hash` in the **request
   body** (via `CustomerCreate`), even though both are generated
   server-side — making the endpoint impossible to call as intended
   without the client fabricating those values itself. Split into a
   client-facing `CustomerCreate` (lat/lng/public_data only).
6. 🟡 `models/user.py`, `models/station_user.py`, `models/vehicle.py` set
   `server_default="CURRENT_TIMESTAMP"` as a plain Python string instead
   of `text("CURRENT_TIMESTAMP")`. MariaDB tolerated this, but it is
   incorrect SQLAlchemy usage — SQLAlchemy may attempt to interpret the
   default as a literal value (reproducible failure under SQLite,
   `ValueError: Invalid isoformat string: 'CURRENT_TIMESTAMP'`). Fixed
   for consistency with the rest of the codebase, which already used
   `text(...)` correctly.

## Dependency Audit & Update (2026-10-02)

### Removed (confirmed unused — not imported anywhere in the codebase)

| Package                                | Reason                                                                                                                      |
|----------------------------------------|-----------------------------------------------------------------------------------------------------------------------------|
| `argon2-cffi` / `argon2-cffi-bindings` | Password hashing uses `bcrypt` directly (`auth/password.py`)                                                                |
| `passlib`                              | Same — unused                                                                                                               |
| `pwdlib`                               | Same — unused                                                                                                               |
| `services==0.1.1`                      | Generic name, zero imports found anywhere; likely a leftover/placeholder                                                    |
| `faker`                                | Added speculatively for future test data generation during the testing pass, never actually used (tests use `uuid` instead) |

Verified by actually uninstalling all six from the virtualenv (not just
removing from `pyproject.toml`) and re-running the full test suite —
89/89 passed, 96.4% coverage, confirming the app has zero runtime
dependency on any of them.

### Kept out of `pyproject.toml`, but still needed — documented separately

`pip` and `uv` are package-management **tools**, not application
dependencies, so they must never appear in `pyproject.toml`'s
`dependencies`. They are still required for development workflows (compiling `requirements.txt`), so they're documented
in
[INSTALL.md § 5 Dependency Tooling](INSTALL.md#5-dependency-tooling-pip--uv)
instead, and `make deps-update`/`make deps-update-package` now
auto-install `uv` into the active venv on first use if missing.
dependency on any of them.

### Upgraded to latest compatible version

| Package         | Before  | After                                     |
|-----------------|---------|-------------------------------------------|
| `fastapi`       | 0.141.1 | 0.142.2                                   |
| `mako`          | 1.4.1   | 1.4.3                                     |
| `pyjwt`         | 2.14.0  | 2.15.1                                    |
| `python-dotenv` | 1.2.3   | 1.2.4                                     |
| `sqlalchemy`    | 2.0.54  | **2.1.2** (minor version bump, 2.0 → 2.1) |
| `starlette`     | 1.6.0   | 1.7.0                                     |
| `uvicorn`       | 0.53.0  | 0.54.0                                    |

Each upgrade was applied one package at a time, followed immediately by a
full test run; every one of the above passed cleanly with no code changes
required. `fastapi`'s upgrade pulled in a new transitive dependency,
`opentelemetry-api==1.45.0`, now pinned explicitly.

### Intentionally NOT upgraded

| Package         | Latest available | Why pinned                                                                                                                                                                                                                                                                                                         |
|-----------------|------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `pydantic-core` | 2.49.0           | `pydantic==2.13.5` (itself already the newest 2.x release) hard-requires `pydantic-core==2.46.5` exactly — installing 2.49.0 standalone breaks pydantic's own import-time version check (`SystemError: installed pydantic-core version is incompatible`). Must wait for a `pydantic` release that raises this pin. |

## Dependency Versioning Strategy Change (2026-10-02, follow-up)

**Problem:** every dependency in `pyproject.toml` — including transitive
ones (`click`, `h11`, `idna`, `cffi`, `mako`, `greenlet`, `anyio`, etc.) —
was pinned with an exact `==`. This blocked `pip`/`uv` from ever
resolving a newer compatible version on its own; every future update
required manually editing a specific version number for every package,
one at a time.

**Fix:** `pyproject.toml` now lists **only direct dependencies** (ones
actually imported by application code — verified via a full-codebase
import scan) with **compatible-release ranges**:
`>=<current>,<<next-major>` instead of `==<exact>`. This means:

- Patch/minor releases are picked up automatically next time
  `make deps-update` is run (e.g. `fastapi>=0.142.2,<1.0.0` will happily
  take `0.143.0` or `0.199.9`, but never `1.x`).
- A library's own major-version bump still requires a deliberate,
  tested decision — bump the upper bound by hand, same one-package-at-a-time
  workflow used in the audit above.
- `requirements.txt` remains a fully-pinned (`==`) lockfile, generated by
  `make deps-update` — it still guarantees reproducible installs; only
  the *source* (`pyproject.toml`) range changed.
- Transitive dependencies are no longer declared by hand in
  `pyproject.toml` — they're resolved and pinned automatically into
  `requirements.txt` by the dependency resolver.

## Dependency Audit Correction (2026-10-02, same day)

After the "only direct imports" rule was applied, `make test`/`make
test-cov` broke on a clean install with:
`RuntimeError: The starlette.testclient module requires the httpx2
package` and (on Windows) `zoneinfo.ZoneInfoNotFoundError: No time zone
found with key Europe/Kyiv`.

**Root cause:** the import scan only looks at `import`/`from` statements
in application code — it cannot see **test-runtime-only** dependencies (`httpx`, required internally by
`fastapi.testclient.TestClient`, never
imported directly by any test file) or **platform-conditional stdlib
dependencies** (`zoneinfo.ZoneInfo(...)` needs IANA tzdata, which Linux/
macOS ship with the OS but Windows does not — hence `tzdata`).

**Fix:** added both back as explicit direct dependencies in
`pyproject.toml`:

- `httpx>=0.28.1,<1.0.0` — unconditional (needed by the test suite on
  every platform).
- `tzdata>=2026.4,<2027.0; sys_platform == 'win32'` — Windows-only via a
  PEP 508 environment marker, so Linux/macOS installs don't carry the
  extra ~350 KB they don't need.

**Lesson:** a static import scan is a good *starting point* for a
dependency audit, but always verify with a clean-install smoke test (`pip install -r requirements.txt` into a fresh
venv, then run the full
test suite) before trusting "this package has zero imports → it's safe
to remove" — some dependencies are consumed indirectly by a framework (`TestClient`) or are platform-specific (`tzdata`
on Windows).

## Test Suite History and Current Coverage

- Before the test-suite work, only `../tests/station/test_stations.py`
  existed, and it depended on a real MariaDB connection with no isolation (shared
  `TestSessionLocal`, no transaction rollback between tests, no fixtures
  for users/auth).
- ✅ Added an isolated SQLite-based test setup (`tests/conftest.py`
  rewritten), per-module test files, and auth/service/customer coverage.
  See [TESTING.md](TESTING.md).
- Earlier runs achieved about 96% statement coverage; the latest measured
  run is **90.2%** with 278 passing tests. See
  [TESTING.md](TESTING.md#coverage) for current results and uncovered areas.
- ✅ Added `make test`, `make test-verbose`, `make test-cov`,
  `make test-cov-html`, `make test-file` targets to the `Makefile`.

## Running Tests Inside Docker (2026-10-02)

**Problem:** tests could only run against the local `.venv`, so every
local-environment issue (missing `pip`/`uv`, a package accidentally
uninstalled, wrong Python version) blocked testing entirely — even
though the `api` container already has a clean, reproducible
environment built from `requirements.txt`.

**Fix, two parts:**

1. `.dockerignore` was excluding `tests/` from the build context, so
   even if you wanted to run tests in the container, they weren't
   there. Removed that line (and excluded coverage artifacts instead —
   `htmlcov/`, `.coverage`, `coverage.xml` — which don't belong in an
   image).
2. `docker/api/entrypoint.sh` had **CRLF line endings** (likely from a
   Windows checkout/edit), which broke its `#!/bin/sh` shebang entirely
   inside the Linux container (`exec .../entrypoint.sh: no such file
   or directory`, endless restart loop). Fixed the line endings and
   added [`.gitattributes`](../.gitattributes) to force `eol=lf` for
   `*.sh`, `Makefile`, `Dockerfile`, and `*.py` so Git never
   reintroduces CRLF on a Windows checkout again.

Initially added as separate `make docker-test*` targets alongside a
local/.venv-based `make test*`; later consolidated into a single set —
`make test`, `make test-cov`, `make test-verbose`, `make test-cov-html`,
`make test-file` — that **always** run inside the `api` container via
`docker compose exec api python -m pytest ...`. There is intentionally
no local/.venv test path anymore: testing the container that actually
ships is the only thing that matters, and it removes any class of
"works on my machine" environment drift entirely. See
[TESTING.md](TESTING.md).

**Bonus bug caught by this:** running tests inside the container
immediately failed with every authenticated endpoint returning 401,
because `tests/conftest.py` used `os.environ.setdefault(...)` for
`COOKIES_SECURE` etc. — which does nothing when `docker-compose.yml`
already injected a real value as an OS-level env var before Python
started. Switched to forcibly overwriting (`os.environ[...] = ...`)
instead, making the test environment identical on bare host and in
container.

## Fixing Test Warnings (2026-10-02)

**Problem:** `make test` produced 52 warnings across the suite:
`StarletteDeprecationWarning` (TestClient wants httpx2), 5×
`PydanticDeprecatedSince20` (class-based `Config` instead of
`ConfigDict`), and `InsecureKeyLengthWarning` (HMAC key under 32 bytes)
from PyJWT on every signed/decoded token.

**Fixes (all resolved properly, not suppressed):**

1. **`StarletteDeprecationWarning`** — `fastapi.testclient.TestClient` is
   now built on `httpx2`; plain `httpx` is deprecated for this purpose.
   Added `httpx2>=2.13.1,<3.0.0` as a direct dependency (alongside the
   still-needed `httpx`) and rebuilt the image (`make up-build`) so
   TestClient picks it up automatically.
2. **`PydanticDeprecatedSince20`** (×5, in `validations/customer.py`,
   `service.py`, `station.py`) — class-based `class Config:
   from_attributes = True` is deprecated since Pydantic V2.0. Replaced
   with `model_config = ConfigDict(from_attributes=True)` in every
   affected schema.
3. **`InsecureKeyLengthWarning`** — `auth/config.py`'s `LoginManager` is
   keyed off `Config.cookie_secret` (`COOKIES_SECRET_KEY`), not
   `JWT_SECRET_KEY` as one might assume from the name. The test secrets
   in `tests/conftest.py` were only 18–34 bytes; PyJWT requires ≥32 bytes
   for HS256 HMAC keys. Lengthened both `JWT_SECRET_KEY` and
   `COOKIES_SECRET_KEY` test values to ≥32 bytes.

**Result at that time:** `make test` / `make test-cov` produced zero
warnings and 89 passed at 96.4% coverage. The latest run has four
dependency deprecation warnings; see [TESTING.md](TESTING.md).
