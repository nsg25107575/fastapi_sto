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

Hashing uses `bcrypt` directly (`auth/password.py`), **not** `passlib` or
`pwdlib`/`argon2-cffi`, even though both are present in the dependency list
— see [ISSUES.md](ISSUES.md) for the resulting cleanup recommendation.

## Secrets

| Env var              | Used for                                                                                            |
|----------------------|-----------------------------------------------------------------------------------------------------|
| `JWT_SECRET_KEY`     | Signs/verifies JWTs (`fastapi-login` `LoginManager(secret=...)`)                                    |
| `COOKIES_SECRET_KEY` | Declared in `Config` but **not currently passed** to the cookie signer — see [ISSUES.md](ISSUES.md) |
| `COOKIES_SECURE`     | Whether the `station` cookie requires HTTPS (`Secure` flag)                                         |

`../config/config.py` currently ships **hardcoded fallback values**
(`"supersecretkey"`) for both `JWT_SECRET_KEY` and `COOKIES_SECRET_KEY` if
the env vars are unset. This is convenient for local development but a
real security risk if ever deployed without overriding them — see
[ISSUES.md](ISSUES.md) (flagged as high priority).

## Known Limitations

- No role/permission system is enforced yet — `routers/auth.py:/me`
  hardcodes `"roles": ["user"]` with a `# TODO: fill real user roles`.
  `station_roles` / `station_users` tables exist but aren't wired to
  authorization checks anywhere.
- No rate limiting on `/auth/sign-in` or `/auth/sign-up` (brute-force /
  credential-stuffing exposure).
- No email verification flow, despite `users.email_verified` existing.
- No password reset / forgot-password flow.
- Session tokens are never cleaned up (`tokens` rows for expired sessions
  are not deleted — see [ISSUES.md](ISSUES.md)).
