# API Reference

Interactive Swagger UI is served at `GET /docs`; the OpenAPI schema is at
`GET /openapi.json`. Both are available only when `APP_ENV=development`.
Protected station-management endpoints require the `station` session cookie
(see [AUTHENTICATION.md](AUTHENTICATION.md)); customer order and chat flows use
the `customer_device` cookie set by `POST /customer`.

Most request and response bodies are JSON. Error responses use the common
`{"success": false, "message": "...", "data": ...}` envelope. Validation
errors return HTTP 422 with a `data` array of `{field, message}` items; rate
limit errors return HTTP 429. Successful resources generally return their
schema directly, while authentication endpoints use the
`{"success": true, "message": "...", "data": ...}` envelope.

## Auth -- `/auth`

| Method | Path             | Auth     | Body               | Description                                                |
|--------|------------------|----------|--------------------|------------------------------------------------------------|
| POST   | `/auth/sign-up`  | --       | `UserCreateSchema` | Register a user, start a session, and set the cookie (201) |
| POST   | `/auth/sign-in`  | --       | `UserLoginSchema`  | Start a session and set the cookie (202)                   |
| POST   | `/auth/sign-out` | Optional | --                 | Revoke the current session and clear the cookie            |
| GET    | `/auth/me`       | Required | --                 | Return the authenticated user's profile                    |

`UserCreateSchema`: `email`, `password` (8-64 characters, including upper-,
lowercase, digit, and special character), and optional `first_name`,
`second_name`, `last_name`. Sign-in and sign-up are limited to five requests
per minute.

## Stations -- `/stations`

| Method | Path                              | Auth     | Description                                                |
|--------|-----------------------------------|----------|------------------------------------------------------------|
| POST   | `/stations/`                      | Required | Create a station owned by the current user                 |
| GET    | `/stations/`                      | --       | Paginated list of non-deleted stations (`limit`, `offset`) |
| GET    | `/stations/nearest`               | --       | Find nearby approved, active stations                      |
| GET    | `/stations/{station_id}`          | --       | Get a station                                              |
| PUT    | `/stations/{station_id}`          | Required | Update a station; the owner only                           |
| DELETE | `/stations/{station_id}`          | Required | Soft-delete a station; the owner only (204)                |
| PUT    | `/stations/{station_id}/moderate` | Admin    | Approve or reject a station                                |

`StationCreateSchema`: `name`, `address`. Coordinates are resolved from the
address using the geocoding service; clients do not provide latitude or
longitude. `StationUpdateSchema` accepts optional `name`, `address`, and
`active`; changing the address triggers geocoding.

`GET /stations/nearest` accepts a JSON `NearestStationsSchema` body containing
`lat` and `lng` (despite using GET). Coordinates must be within latitude
`[-90, 90]` and longitude `[-180, 180]`. Results include distance, rating,
review count, and services ordered by price.

Create/update return `409 Conflict` for a duplicate `(name, address)` and
`400 Bad Request` when address geocoding fails. A missing or soft-deleted
station returns `404`. The moderation request uses
`{ "moderation_status": "approved" | "rejected", "rejection_reason": ... }`;
approving clears any rejection reason.

## Station contacts -- `/station-contacts`

| Method | Path                             | Auth     | Description                                          |
|--------|----------------------------------|----------|------------------------------------------------------|
| POST   | `/station-contacts/`             | Required | Create a contact for an accessible station           |
| GET    | `/station-contacts/`             | --       | Paginated contact list; optional `station_id` filter |
| GET    | `/station-contacts/{contact_id}` | --       | Get a contact                                        |
| PUT    | `/station-contacts/{contact_id}` | Required | Update a contact                                     |
| DELETE | `/station-contacts/{contact_id}` | Required | Delete a contact                                     |

The station owner or an assigned employee with the `station_contact.manage`
permission may create, update, or delete contacts. Creation accepts
`station_id`, `type`, and `value`; updates accept optional `type` and `value`.

## Services -- `/services`

| Method | Path                     | Auth     | Description                              |
|--------|--------------------------|----------|------------------------------------------|
| POST   | `/services/`             | Required | Add a service to a station               |
| GET    | `/services/`             | --       | Paginated list of distinct service names |
| GET    | `/services/{service_id}` | --       | Get a service                            |
| PUT    | `/services/{service_id}` | Required | Update a service                         |
| DELETE | `/services/{service_id}` | Required | Delete a service                         |

Create accepts a JSON body with `station_id`, `name`, and optional `price`;
update accepts optional `name` and `price`. The owner or a station employee
with `service.manage` permission may manage services. Changing a service
resets its station's moderation status to pending.

## Customer -- `/customer`

| Method | Path         | Auth | Description                                          |
|--------|--------------|------|------------------------------------------------------|
| POST   | `/customer/` | --   | Record customer location and return the new customer |

The request body contains `lat`, `lng`, and `public_data`. The server derives
the IP from the request and generates a `device_hash`; the response includes
both and the customer `id`. The endpoint also sets the HTTP-only
`customer_device` cookie used to authorize the customer's order and chat
requests.

## Orders -- `/orders`

| Method | Path                        | Auth                               | Description                                           |
|--------|-----------------------------|------------------------------------|-------------------------------------------------------|
| POST   | `/orders/`                  | --                                 | Place an order for a station service                  |
| GET    | `/orders/{order_id}`        | Customer cookie or station session | Get an order the caller may access                    |
| PUT    | `/orders/{order_id}/status` | Required                           | Update order status; owner or `order.manage` employee |

`OrderCreateSchema`: `customer_id` (from `POST /customer`), `station_id`, and
`station_service_id` (from a station result). The service must belong to the
specified station. `OrderStatusUpdateSchema.status` is one of `pending`,
`confirmed`, `in_progress`, `completed`, `rejected`, or `cancelled`.

Anonymous customers can read only their own orders, verified using the
`customer_device` cookie. Station owners and employees with `order.manage`
permission can read orders for their station. Missing orders return `404`;
invalid customer/service references return `400`; unauthorized access returns
`401` or `403`.

## Chat -- `/chat`

| Method | Path                                  | Auth                     | Description        |
|--------|---------------------------------------|--------------------------|--------------------|
| POST   | `/chat/rooms/{chat_room_id}/messages` | Owning customer's cookie | Send a message     |
| GET    | `/chat/rooms/{chat_room_id}/messages` | Owning customer's cookie | List room messages |

The message request contains a non-empty `body` and optional
`attachment_url`. A customer can access only the chat room associated with
their order. Sending a message to an archived room is rejected.

## Reviews -- `/reviews`

| Method | Path        | Auth | Description                           |
|--------|-------------|------|---------------------------------------|
| POST   | `/reviews/` | --   | Create a review for a completed order |

`ReviewCreateSchema` contains `order_id`, `rating` (1-5), and optional
`comment`. The order must exist, be completed, and not already have a review.

## Entities without API routes

Models exist, but no routes currently expose standalone CRUD for
`station_customers`, `station_roles`/`station_users`, `station_work_schedule`,
`vehicles`, or `fuel_types`. Station employee permissions are enforced by the
authorization layer; role assignment itself has no API endpoint.
