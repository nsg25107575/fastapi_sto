# Issues & Improvement Backlog

Tasks identified from a full codebase review (2026-10-02). Each task is
scoped to be small and independently actionable. Priority: 🔴 High (security
or correctness bug) · 🟡 Medium (robustness/consistency) · 🟢 Low (polish).

## Security

### 🔴 ISSUE-1: Hardcoded fallback secrets in `config.py`
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
`exceptions.py` messages are English. Inconsistent for API consumers.
**Fix:** move service-not-found to a named exception in `exceptions.py`,
in English, consistent with the rest.

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

## Dependency Hygiene

### 🟢 ISSUE-13: Redundant password-hashing libraries
`passlib`, `pwdlib`, and `argon2-cffi` are all declared dependencies, but
`auth/password.py` uses `bcrypt` directly. Dead weight in the image and a
larger attack surface to patch.
**Fix:** confirm nothing else uses `passlib`/`pwdlib`/`argon2-cffi` and
remove them from `pyproject.toml`/`requirements.txt` (`make deps-update`
after).

### 🟢 ISSUE-14: `services==0.1.1` dependency unclear
A generically-named `services` package is pinned; unclear what it's used
for (not imported anywhere found during review).
**Fix:** confirm usage with the team; remove if unused.

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

## Testing Gaps (addressed in this pass)

- Prior to this pass, only `tests/test_stations.py` existed, and it
  depended on a real MariaDB connection with no isolation (shared
  `TestSessionLocal`, no transaction rollback between tests, no fixtures
  for users/auth).
- ✅ Added an isolated SQLite-based test setup (`tests/conftest.py`
  rewritten), per-module test files, and auth/service/customer coverage.
  See [TESTING.md](TESTING.md).
