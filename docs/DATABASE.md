# Database Schema & Migrations

## Engine

- **Database:** MariaDB (latest), accessed via the `mariadb` Python
  connector (SQLAlchemy dialect `mariadb+mariadbconnector`).
- **ORM:** SQLAlchemy 2.x, declarative style (`Mapped[...]` / `mapped_column`).
- **Migrations:** Alembic, autogeneration-driven. Migration scripts live in
  [`alembic/versions/`](../alembic/versions/).
- **Connection pool:** configured in `database/engine.py` — `pool_size`,
  `max_overflow`, `pool_timeout`, `pool_recycle`, `pool_pre_ping`, all
  overridable via `DB_POOL_*` env vars (see [INSTALL.md](INSTALL.md)).

## Entity-Relationship Summary

```
users ──1───N── stations ──1───N── station_services
  │                 │
  │                 ├──N── station_contacts
  │                 ├──N── station_customers ──N───1── users
  │                 └──N── station_work_schedule
  │
  ├──N── station_users ──N───1── station_roles
  ├──N── tokens
  └──N── vehicles ──N───1── fuel_types

customers  (standalone — anonymous geolocation capture, no FK to users)
```

## Tables

### `users`
| Column                               | Type              | Notes                                                   |
|--------------------------------------|-------------------|---------------------------------------------------------|
| id                                   | PK, autoincrement |                                                         |
| email                                | varchar(100)      | unique, not null                                        |
| email_verified                       | datetime(tz)      | nullable                                                |
| first_name / second_name / last_name | varchar(100)      | nullable                                                |
| password                             | varchar(256)      | bcrypt hash, not null                                   |
| created_at / updated_at              | datetime(tz)      | server default `CURRENT_TIMESTAMP`                      |
| deleted_at                           | datetime(tz)      | nullable (not currently enforced via `SoftDeleteMixin`) |

### `stations`
| Column                  | Type              | Notes                                              |
|-------------------------|-------------------|----------------------------------------------------|
| id                      | PK, autoincrement |                                                    |
| user_id                 | FK → users.id     | not null (owner)                                   |
| name                    | varchar(100)      | not null                                           |
| address                 | varchar(200)      | not null                                           |
| active                  | boolean           | default `1`                                        |
| latitude / longitude    | numeric(16,14)    | nullable                                           |
| created_at / updated_at | datetime(tz)      | server default `CURRENT_TIMESTAMP`                 |
| deleted_at              | datetime(tz)      | nullable — **soft delete** (see `SoftDeleteMixin`) |

Constraints/indexes:
- `UNIQUE (name, address)` — `uq_station_name_per_address`
- `INDEX (address)` — `idx_station_address`
- `INDEX (latitude, longitude)` — `idx_station_latitude_longitude`
- `FULLTEXT INDEX (name)` — `idx_station_name_fulltext` (MariaDB-specific;
  powers `StationModel.search_stations_by_name`)

### `station_services`
Per-station price list. `station_id` FK → `stations.id`, `name`
varchar(200), `price` numeric(12,2) nullable, timestamps.
Index on `name`.

### `station_contacts`
`station_id` FK, `type` varchar(50), `value` varchar(255), timestamps.
Indexes on `type` and `value`.

### `station_customers`
Links a `station` to a `user` with a unique `phone` and a
`problem_description` (text). `UNIQUE INDEX (phone)`.

### `station_roles`
Simple lookup table: `name`, `description` (nullable text), timestamps.

### `station_users`
Assigns a `user` to a `station` with a `role_id` (defaults to `1`).
`UNIQUE (station_id, user_id)`.

### `station_work_schedule`
`station_id` FK, `flow` (nullable text — intended for a schedule
definition, format not yet formalized — see [ISSUES.md](ISSUES.md)).

### `tokens`
`user_id` FK → users.id, `token` varchar(512), `expires_at` datetime(tz)
(defaults to **now + 7 days** at the application layer, independent of the
JWT's own `exp` claim). Used by `auth/dependencies.py` to validate sessions
against the database (enables server-side revocation on sign-out).

### `customers`
Anonymous geolocation capture (not tied to `users`): `ip` varchar(45),
`device_hash` varchar(36), `lat`/`lng` numeric(16,14), `public_data` JSON.

### `vehicles` / `fuel_types`
`fuel_types`: simple lookup (`name`, unique).
`vehicles`: `user_id` FK, `fuel_type_id` FK (default `1`), `make`, `model`,
`year`, `license_plate`, timestamps.

## Soft Delete

Only `StationModel` currently mixes in `SoftDeleteMixin`. See
[ARCHITECTURE.md](ARCHITECTURE.md#soft-delete-pattern-stationmodel) for how
the global filter works. `UserModel` has a `deleted_at` column but does
**not** use the mixin/global filter yet — see [ISSUES.md](ISSUES.md).

## Running Migrations

`make migrate-*` targets run inside the `api` container (requires it to
be running — `make up`/`make up-build` first):

```bash
# Apply all pending migrations
make migrate-up

# Revert all migrations
make migrate-down

# Apply/revert a specific migration by revision id
make migrate-up-index index="<revision>"
make migrate-down-index index="<revision>"
```

Inside Docker, migrations run **automatically** on every `api` container
start via `docker/api/entrypoint.sh` (`alembic upgrade head`), followed by
all seeders (`python -m seeders`). No manual migration or seed step is needed
for the containerized workflow.

### Creating a New Migration

Also run inside the container (via its own `make` target):

```bash
make migrate msg="describe the schema change"
```

Always review the autogenerated script before committing — Alembic's
autogeneration does not reliably detect every change (e.g. some
MariaDB-specific index types, server-side defaults, or renames).

## Seeding Data

When running natively, apply migrations first, then run the idempotent
lookup-data seeders:

```bash
make seed                         # run all seeders
make seed seeder=station_roles    # seed station roles only
make seed seeder=fuel_types       # seed fuel types only
make seeder-create name=ExampleSeeder
make seeder-list
make seeder-run seeder=example
make seeder-run-all
```

`seeders/` contains the runner and shared seeder code; individual seeders are
kept separately in [`seeders/content/`](../seeders/content/).
`seeder-create` generates an editable Python file in that content directory.
Open it in your editor and implement `Seeder.run(session)` with the models and
seed data you need. For example, after `make seeder-create name=ExampleSeeder`,
edit `seeders/content/example_seeder.py`.
The seeder is then available to list and run individually, and is included in
the default all-seeders command. Existing lookup rows are preserved; only
missing names are inserted. The command wraps each run in a database
transaction, so a failure rolls back that run.

## Known Gaps

- `station_work_schedule.flow` has no defined schema/format.
