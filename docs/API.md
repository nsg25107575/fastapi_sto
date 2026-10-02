# API Reference

Interactive Swagger UI is served at `GET /docs` (custom page, see
`main.py`); the raw OpenAPI schema is at `GET /openapi.json`.

All request/response bodies are JSON unless noted. Protected endpoints
require the `station` session cookie (see [AUTHENTICATION.md](AUTHENTICATION.md)).

## Auth — `/auth`

| Method | Path             | Auth              | Body               | Description                                   |
|--------|------------------|-------------------|--------------------|-----------------------------------------------|
| POST   | `/auth/sign-up`  | —                 | `UserCreateSchema` | Register a new user, auto-login (sets cookie) |
| POST   | `/auth/sign-in`  | —                 | `UserLoginSchema`  | Log in, sets session cookie                   |
| POST   | `/auth/sign-out` | cookie (optional) | —                  | Invalidate current session, clears cookie     |
| GET    | `/auth/me`       | **required**      | —                  | Current authenticated user's profile          |

`UserCreateSchema`: `email`, `password` (8–64 chars, upper+lower+digit+special),
`first_name?`, `second_name?`, `last_name?`.

`UserLoginSchema`: `email`, `password`.

## Stations — `/stations`

| Method | Path                     | Auth         | Description                                                       |
|--------|--------------------------|--------------|-------------------------------------------------------------------|
| POST   | `/stations/`             | **required** | Create a station owned by the current user                        |
| GET    | `/stations/`             | —            | List all (non-deleted) stations                                   |
| GET    | `/stations/nearest`      | —            | Nearest active stations by coordinates (query body: `lat`, `lng`) |
| GET    | `/stations/{station_id}` | —            | Get a single station                                              |
| PUT    | `/stations/{station_id}` | **required** | Update a station (partial)                                        |
| DELETE | `/stations/{station_id}` | **required** | Soft-delete a station                                             |

Notes:
- `POST`/`PUT` return `409 Conflict` if the `(name, address)` pair already
  exists (`DuplicateStationException`).
- `GET /stations/{id}` and `PUT`/`DELETE` return `404 Not Found`
  (`StationNotFoundException`) if the station doesn't exist (or is
  soft-deleted).
- `GET /stations/nearest` validates `lat ∈ [-90, 90]`, `lng ∈ [-180, 180]`,
  returning `400 Bad Request` (`InvalidCoordinateException`) otherwise. The
  result includes each station's `services` sorted by price.
- **Ownership is not currently enforced** on `PUT`/`DELETE` — any
  authenticated user can modify or delete *any* station, not just their
  own. See [ISSUES.md](ISSUES.md) (flagged as high priority).

## Services — `/services`

Per-station price list entries.

| Method | Path                     | Auth         | Description                                                       |
|--------|--------------------------|--------------|-------------------------------------------------------------------|
| POST   | `/services/`             | **required** | Create a service (query params: `station_id`, `name`, `price?`)   |
| GET    | `/services/`             | —            | List services, aggregated by name (min/max price across stations) |
| GET    | `/services/{service_id}` | —            | Get a single service                                              |
| PUT    | `/services/{service_id}` | **required** | Update a service (query params)                                   |
| DELETE | `/services/{service_id}` | **required** | Delete a service                                                  |

Notes:
- Returns `404` with a Russian-language message (`"Услуга не найдена"`) if
  not found — inconsistent with the rest of the API's English messages;
  see [ISSUES.md](ISSUES.md).
- Request parameters are plain **query parameters**, not a JSON body
  (inconsistent with `/stations` and `/auth`, which use Pydantic request
  bodies) — see [ISSUES.md](ISSUES.md).
- `station_id` is not validated to exist before creating a service.

## Customer — `/customer`

Anonymous geolocation capture (not a `user` account).

| Method | Path         | Auth | Description                                                                                         |
|--------|--------------|------|-----------------------------------------------------------------------------------------------------|
| POST   | `/customer/` | —    | Record a customer's IP, coordinates, and arbitrary `public_data`, returns a generated `device_hash` |

`CustomerCreate`: `lat`, `lng`, `public_data` (free-form dict). `ip` and
`device_hash` are generated server-side (`ip` from `request.client.host`,
`device_hash` is a random 36-char string).

> ⚠️ `request.client.host` is unreliable behind a reverse proxy/load
> balancer (returns the proxy's IP, not the real client IP) unless
> `X-Forwarded-For` is parsed. See [ISSUES.md](ISSUES.md).

## Error Response Shape

Most success responses use a `{"detail": [{"type": "success", "msg": "..."}]}`
envelope (see `routers/auth.py`). Error responses follow FastAPI's default
`{"detail": "<message>"}` shape (via `HTTPException`). **These two shapes
are inconsistent** — see [ISSUES.md](ISSUES.md).

## Endpoints Not Yet Implemented

Models exist for the following entities, but no router currently exposes
them via the API:
- `station_contacts`
- `station_customers`
- `station_roles` / `station_users` (role assignment)
- `station_work_schedule`
- `vehicles` / `fuel_types`

See [ISSUES.md](ISSUES.md) for tracked follow-up tasks.
