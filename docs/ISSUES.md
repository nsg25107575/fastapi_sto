# Issues & Improvement Backlog

Tasks identified from full codebase reviews (2026-10-02). Each task is
scoped to be small and independently actionable. Priority: 🔴 High (security
or correctness bug) · 🟡 Medium (robustness/consistency) · 🟢 Low (polish).

## Security

### 🔴 ISSUE-1: Hardcoded fallback secrets in `config/config.py`
`JWT_SECRET_KEY` and `COOKIES_SECRET_KEY` fall back to the literal string
`"supersecretkey"` when the env var is unset. If the app is ever deployed
without explicitly setting these, every token/cookie is forgeable.
**Fix:** raise at startup if `APP_ENV=production` and either secret is
unset or equals the default placeholder.

### 🔴 ISSUE-2: Station ownership not enforced on update/delete
`PUT /stations/{id}` and `DELETE /stations/{id}` only require *some*
authenticated user — not the station's owner (`station.user_id`). Any
logged-in user can edit or delete any other user's station.
**Fix:** compare `current_user.id == station.user_id` in
`routers/stations.py`, raise `403 Forbidden` otherwise.

### 🟡 ISSUE-3: `COOKIES_SECRET_KEY` declared but unused
`Config.cookie_secret` is read from env but never passed to
`fastapi-login`'s `LoginManager` or used to sign the cookie separately from
the JWT itself — it's effectively dead config, which is misleading.
**Fix:** either wire it into cookie signing or remove it and document that
`JWT_SECRET_KEY` alone secures the session.

### 🟡 ISSUE-4: No rate limiting on auth endpoints
`/auth/sign-in` and `/auth/sign-up` have no throttling — vulnerable to
credential stuffing / brute force.
**Fix:** add `slowapi` (or similar) rate limiting, e.g. 5 attempts/min/IP.

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

### 🟡 ISSUE-7: Mixed request styles (query params vs. JSON body)
`routers/service.py` uses plain query parameters (`station_id`, `name`,
`price`) while `routers/stations.py` and `routers/auth.py` use Pydantic
request bodies. Inconsistent and harder to validate/document.
**Fix:** add `ServiceCreateSchema` / `ServiceUpdateSchema` in
`validations/service.py` and switch `routers/service.py` to JSON bodies.

### 🟡 ISSUE-8: Mixed-language error messages
`routers/service.py` raises `"Услуга не найдена"` (Russian) while
`exceptions/exceptions.py` messages are English. Inconsistent for API
consumers. **Fix:** move service-not-found to a named exception in
`exceptions/exceptions.py`, in English, consistent with the rest.

### 🟡 ISSUE-9: Inconsistent success/error response envelopes
Success responses in `routers/auth.py` use
`{"detail": [{"type": "success", "msg": ...}]}`; errors use FastAPI's
default `{"detail": "<str>"}`. Two different shapes for `detail`.
**Fix:** pick one consistent response envelope (recommend a shared
`APIResponse` Pydantic model) and apply it everywhere.

### 🟡 ISSUE-10: `UserModel` has `deleted_at` but no soft-delete behavior
`users.deleted_at` exists but `UserModel` doesn't mix in `SoftDeleteMixin`,
so the column is unused and deleted users would still authenticate/appear
in queries if ever set.
**Fix:** either wire up `SoftDeleteMixin` for `UserModel` or remove the
unused column via a migration.

### 🟢 ISSUE-11: `station_id` not validated in `services` router
`POST /services/` accepts any `station_id` without checking the station
exists — creates orphaned/invalid rows if given a bad id.
**Fix:** look up the station first, raise `StationNotFoundException` if
missing.

### 🟢 ISSUE-12: Unused imports / duplicate `get_current_user` definitions
`routers/auth.py` defines a local `get_current_user` endpoint handler with
the **same name** as the dependency function in `auth/dependencies.py` —
not a bug (different scopes/usages) but confusing to read.
**Fix:** rename the route handler, e.g. `get_me`.

### 🟡 ISSUE-18: Inconsistent session acquisition (`get_session` vs. global `engine`)

`routers/stations.py`, `routers/customer.py`, `routers/service.py` all use
`Session = Depends(get_session)`; `routers/auth.py` instead opens
`with Session(engine) as session:` using the module-level `engine` from
`database.engine` directly. This bypasses `app.dependency_overrides`,
which the test suite had to work around via monkey-patching (see
[TESTING.md](TESTING.md)) — a sign it's also harder to reason about/mock
in production. **Fix:** refactor `routers/auth.py` to accept `session: Session =
Depends(get_session)` like every other router.

## Dependency Hygiene

### ✅ ISSUE-13 (RESOLVED 2026-10-02): Redundant password-hashing libraries
`passlib`, `pwdlib`, and `argon2-cffi` are all declared dependencies, but
`auth/password.py` uses `bcrypt` directly. Dead weight in the image and a
larger attack surface to patch. **Fix:** confirmed unused anywhere in the codebase; removed from
`pyproject.toml`/`requirements.txt`. See [dependency audit](#dependency-audit--update-2026-10-02) below.

### ✅ ISSUE-14 (RESOLVED 2026-10-02): `services==0.1.1` dependency unclear
A generically-named `services` package is pinned; unclear what it's used
for (not imported anywhere found during review). **Fix:** confirmed unused anywhere in the codebase; removed.

## Feature Gaps

### 🟢 ISSUE-15: No endpoints for station_contacts / station_customers / station_users / station_roles / vehicles
Models and migrations exist but no router exposes them — likely planned
but not yet built.
**Fix:** scope and implement CRUD routers per entity as separate tickets
once prioritized.

### 🟢 ISSUE-16: No role/permission enforcement
`station_roles` / `station_users` exist but nothing checks a user's role
before allowing station mutations (ties into ISSUE-2).
**Fix:** design an authorization layer once ownership checks (ISSUE-2) are
in place.

### 🟢 ISSUE-17: No email verification or password reset flow
`users.email_verified` column exists but is never set; no
forgot-password endpoint.
**Fix:** scope as a follow-up feature (needs an email-sending capability
first).

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

## Testing Gaps (addressed in this pass)

- Prior to this pass, only `tests/test_stations.py` existed, and it
  depended on a real MariaDB connection with no isolation (shared
  `TestSessionLocal`, no transaction rollback between tests, no fixtures
  for users/auth).
- ✅ Added an isolated SQLite-based test setup (`tests/conftest.py`
  rewritten), per-module test files, and auth/service/customer coverage.
  See [TESTING.md](TESTING.md).
- ✅ Achieved ~96% statement coverage on application code (target was
  80%) — see [TESTING.md](TESTING.md#coverage).
- ✅ Added `make test`, `make test-verbose`, `make test-cov`,
  `make test-cov-html`, `make test-file` targets to the `Makefile`.
