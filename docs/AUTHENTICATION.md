# Authentication

## Overview

Authentication combines **JWT** (via [`fastapi-login`](https://github.com/MushroomMaula/fastapi_login))
with **server-side session persistence** (a `tokens` DB table), delivered
to the browser as an `httponly` cookie.

This is a hybrid model: stateless JWT validation (signature + expiry)
*plus* a stateful lookup, so that signing out immediately invalidates a
session rather than waiting for the JWT to expire naturally.

## Components

| File                   | Responsibility                                                                                                        |
|------------------------|-----------------------------------------------------------------------------------------------------------------------|
| `auth/config.py`       | `LoginManager` instance (`manager`), cookie parameters (`COOKIE_PARAMS`)                                              |
| `auth/dependencies.py` | `load_user` (token → `UserModel`, with DB-backed expiry check), `get_current_user` dependency                         |
| `auth/password.py`     | `bcrypt`-based password hashing (`get_password_hash`) and verification (`verify_password`)                            |
| `models/token.py`      | `TokenModel` — persisted session tokens, `save_token` classmethod                                                     |
| `routers/auth.py`      | `/auth/sign-up`, `/auth/sign-in`, `/auth/sign-out`, `/auth/me`                                                        |
| `validations/user.py`  | `UserCreateSchema`, `UserLoginSchema`, `UserUpdateSchema` — includes password-strength and name-formatting validators |

## Flow

### Sign Up (`POST /auth/sign-up`)
1. Validate payload via `UserCreateSchema` (email format, password
   strength: ≥8 chars, upper+lower+digit+special char; name fields are
   trimmed/capitalized and restricted to letters/hyphens/apostrophes).
2. Hash the password with `bcrypt` (`get_password_hash`).
3. Create the `UserModel` row and a `TokenModel` row in **one transaction**.
4. Issue a JWT via `manager.create_access_token(...)` and set it as an
   `httponly`, `samesite=lax` cookie named `station`.
5. On duplicate email, roll back and raise `duplicate_email_exception()` (409).

### Sign In (`POST /auth/sign-in`)
1. Validate payload via `UserLoginSchema`.
2. Look up the user by email; verify password with `verify_password`.
3. On failure, raise `fastapi_login`'s `InvalidCredentialsException`
   (401).
4. On success, issue a new JWT, persist it in `tokens`, set the cookie.

### Sign Out (`POST /auth/sign-out`)
1. Read the `station` cookie value.
2. Delete the matching row from `tokens` (if present) — this is what makes
   the session unusable even though the JWT itself hasn't expired.
3. Delete the cookie from the client.

### Authenticated Requests
- Routers that require authentication declare
  `Depends(get_current_user)` (as a return value) or
  `dependencies=[Depends(get_current_user)]` (as a gate only).
- `fastapi-login`'s `manager` dependency extracts the cookie, calls
  `auth/dependencies.py:load_user(email)` — which **also** requires a
  matching, non-expired `tokens` row — and returns the `UserModel`, or
  raises `401 Unauthorized` automatically if validation fails.

### `GET /auth/me`
Returns the current authenticated user's profile. Protected via
`Depends(manager)` directly (equivalent to `get_current_user`).

## Password Policy

Enforced in `validations/user.py` via `field_validator`:
- Minimum 8, maximum 64 characters.
- At least one digit, one uppercase letter, one lowercase letter, one
  special character (`!@#$%^&*(),.?":{}|<>`).

Hashing uses `bcrypt` directly (`auth/password.py`).

## Secrets

| Env var                  | Used for                                                       |
|--------------------------|----------------------------------------------------------------|
| `JWT_SECRET_KEY`         | Signs/verifies JWTs and therefore secures the `station` cookie |
| `COOKIES_SECURE`         | Controls the cookie `Secure` attribute                         |
| `MAX_COOKIE_AGE_IN_DAYS` | Sets the JWT/cookie lifetime used by `LoginManager`            |

`COOKIES_SECRET_KEY` is not read by the application; `JWT_SECRET_KEY` is the
signing key. In production, startup rejects a missing/default
`JWT_SECRET_KEY`. The development fallback (`"supersecretkey"`) must not be
used in production. `JWT_EXPIRES_IN` is present in configuration but is not
currently wired into `LoginManager`; expiry follows
`MAX_COOKIE_AGE_IN_DAYS`. See [ISSUES.md](ISSUES.md) for configuration
follow-ups.

## Known Limitations

- `/auth/me` currently returns `"roles": ["user"]`; it does not report
  station-specific employee roles. Station-management routes do enforce
  owner and configured employee permissions via `auth/authorization.py`.
- `/auth/sign-in` and `/auth/sign-up` are limited to five requests per minute
  using SlowAPI.
- No email verification flow, despite `users.email_verified` existing.
- No password reset / forgot-password flow.
- Session tokens are never cleaned up (`tokens` rows for expired sessions
  are not deleted — see [ISSUES.md](ISSUES.md)).
