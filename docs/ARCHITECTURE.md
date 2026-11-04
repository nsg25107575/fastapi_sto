# Architecture Overview

## Purpose

KWS Station API is a FastAPI backend for discovering and managing vehicle
service stations ("STO"): station CRUD, nearby-station search by
coordinates, per-station services (price list), customer geolocation
capture, and JWT/cookie-based user authentication.

## Request Flow

```
Client
  │
  ▼
FastAPI app (main.py)
  │
  ├── routers/auth.py        /auth/*       — sign-up, sign-in, sign-out, me
  ├── routers/stations.py    /stations/*   — station CRUD + nearest search
  ├── routers/station_contact.py /station-contacts/* — station contacts
  ├── routers/service.py     /services/*   — per-station price list CRUD
  └── routers/customer.py    /customer/*   — anonymous geolocation capture
      routers/order.py       /orders/*     — customer orders and status
      routers/chat.py        /chat/*       — customer order messages
      routers/review.py      /reviews/*    — completed-order reviews
         │
         ▼
   validations/*.py   — Pydantic request/response schemas (input validation)
         │
         ▼
   models/*.py         — SQLAlchemy ORM models + classmethod query helpers
         │                 (business logic lives here, not in routers)
         ▼
   database/engine.py  — SQLAlchemy Engine + sessionmaker (connection pool)
         │
         ▼
   MariaDB
```

## Layering Convention

- **`routers/`** — HTTP concerns only: parse request, call a model
  classmethod, map result/errors to an HTTP response. No business logic.
- **`validations/`** — Pydantic schemas for request bodies and response
  shapes. Field-level validation (e.g. password strength, name formatting)
  lives here via `@field_validator`.
- **`models/`** — SQLAlchemy ORM models. Business/query logic is
  implemented as `@classmethod`s on the model (e.g.
  `StationModel.read_nearest_stations`, `StationModel.create_station`).
  Models receive an explicit `Session` — they never open their own.
- **`auth/`** — Authentication primitives: `fastapi-login` manager config
  (`auth/config.py`), password hashing (`auth/password.py`), and the
  `get_current_user` FastAPI dependency (`auth/dependencies.py`).
- **`database/`** — Engine/session construction (`engine.py`).
- **`../config/config.py`** — Single source of truth for environment-derived
  settings, exposed as a `Config` dataclass.

## Key Modules

| Module                        | Responsibility                                                                                                              |
|-------------------------------|-----------------------------------------------------------------------------------------------------------------------------|
| `main.py`                     | FastAPI app instance, router registration, custom `/docs` page                                                              |
| `../config/config.py`         | Environment variable loading, `DATABASE_URL` resolution                                                                     |
| `database/engine.py`          | SQLAlchemy `Engine` (connection pool) + `get_session` dependency                                                            |
| `auth/config.py`              | `fastapi-login` `LoginManager` instance, cookie parameters                                                                  |
| `auth/dependencies.py`        | `load_user` (token → user) and authenticated/optional user dependencies; `load_user` opens a session from the shared engine |
| `auth/password.py`            | `bcrypt` password hashing/verification                                                                                      |
| `models/station.py`           | Station CRUD, full-text name search, nearest-station geo query, soft delete                                                 |
| `models/station_service.py`   | Per-station price list CRUD + aggregated price ranges                                                                       |
| `models/user.py`              | User lookup/creation                                                                                                        |
| `models/token.py`             | Session token persistence (DB-backed, not stateless JWT-only)                                                               |
| `../exceptions/exceptions.py` | Centralized `HTTPException` instances reused across routers                                                                 |

## Data Model Summary

See [DATABASE.md](DATABASE.md) for the full schema. Core entities:

- **users** — account/credentials.
- **stations** — a service station owned by a `user` (soft-deletable,
  geo-indexed, full-text indexed by name).
- **station_services** — a station's price list (name + price).
- **station_contacts**, **station_customers**, **station_roles**,
  **station_users**, **station_work_schedule** — station-adjacent entities
  for contacts, assigned staff/roles, linked customers, and work schedules.
  Station contacts have CRUD routes; station employee roles/permissions are
  checked by the authorization layer, but role assignment and the remaining
  entities have no standalone routes.
- **tokens** — issued session tokens, DB-persisted so sessions can be
  revoked server-side (sign-out deletes the row).
- **customers** — anonymous geolocation capture tied to a generated
  `device_hash`, not a `user`.
- **vehicles**, **fuel_types** — user-owned vehicles and fuel types. Models
  exist, but no routes expose them yet.

## Soft Delete Pattern (`StationModel`)

`StationModel` mixes in `SoftDeleteMixin` (`deleted_at: datetime | None`).
A global SQLAlchemy event listener (`do_orm_execute` in `models/station.py`)
automatically appends a `deleted_at IS NULL` filter to every `SELECT`
against any model using `SoftDeleteMixin`, including through
`relationship()` loads (`propagate_to_loaders=True`). To intentionally
include soft-deleted rows, pass `.execution_options(include_deleted=True)`
on the query.

## Authentication Model

- Login issues a JWT (via `fastapi-login`), delivered **both** as an
  `httponly` cookie (`station`) and persisted as a row in `tokens`
  (`TokenModel`).
- `auth/dependencies.py:load_user` validates incoming tokens by requiring a
  **matching, non-expired row in `tokens`** — not just JWT signature
  validity. This means sign-out (which deletes the token row) immediately
  invalidates the session server-side, unlike pure stateless JWT.
- `get_current_user` is the FastAPI dependency routers use to require
  authentication (`Depends(get_current_user)`).

See [AUTHENTICATION.md](AUTHENTICATION.md) for full details.

## Deployment Topology

See [../README.md](../README.md) and [INSTALL.md](INSTALL.md) for the full
picture. In short: `docker/api/` contains the `api` + `db` (MariaDB)
Compose stack; `docker/api/entrypoint.sh` applies Alembic migrations
automatically on container start before launching Uvicorn with multiple
workers.
