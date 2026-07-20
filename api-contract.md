# API Contract

Base URL: `http://localhost:8000`  
All API routes are prefixed with `/api`.  
Interactive docs: `GET /docs` (Swagger UI).

## Error Response Shape

All API errors return a single consistent JSON shape:

```json
{
  "error": {
    "code": "string",
    "message": "human-readable summary",
    "details": {}
  }
}
```

`details` may be a JSON object, an array (Pydantic validation errors), or `null`.

### HTTP Status Code Policy

| Code | When | Example `error.code` values |
|------|------|----------------------------|
| **401** | Missing, invalid, or expired JWT on a protected endpoint; invalid login credentials | `unauthorized` |
| **403** | Authenticated but not permitted for this action (role rule) | `forbidden` |
| **422** | Request body or query params fail schema validation (missing fields, wrong types, out-of-range lengths, invalid enum strings) | `validation_error` |
| **404** | Referenced resource does not exist (ticket, user) | `not_found` |
| **409** | Business-rule conflict — valid JSON but operation not allowed | `invalid_transition`, `ticket_not_editable`, `comment_not_allowed` |

### Authentication

Protected endpoints require a JWT bearer token:

```http
Authorization: Bearer <access_token>
```

Obtain a token via `POST /api/auth/login`. Token lifetime is configured by `JWT_EXPIRE_MINUTES` (default 24 hours).

**Public endpoints (no auth):** `GET /api/health`, `GET /api/users`, `GET /api/tickets`, `GET /api/tickets/{id}`, `GET /api/tickets/{id}/comments`, `POST /api/auth/login`.

**Protected endpoints (auth required):** `POST /api/tickets`, `PATCH /api/tickets/{id}`, `POST /api/tickets/{id}/status`, `POST /api/tickets/{id}/comments`, `GET /api/tickets/export`, `GET /api/auth/me`.

**Deliberate choice — public reads:** For this internal tool, read endpoints (`GET /api/tickets`, `GET /api/tickets/{id}`, `GET /api/tickets/{id}/comments`, and `GET /api/users`) are **intentionally unauthenticated** so anyone on the network can browse tickets and pick assignees. All mutations (`POST`/`PATCH` on tickets, status changes, comments) require a valid JWT. CSV export also requires a JWT and derives the exported user from the token — it does not accept a `created_by` query parameter, so callers cannot download another user's ticket export by guessing an id.

**Role rules (403 when violated):**

| Action | Admin / Agent / Manager | Requester |
|--------|-------------------------|-----------|
| Change status | Allowed | **Forbidden** |
| Create ticket | Allowed; `created_by` set from token | Allowed; `created_by` set from token |
| Edit ticket | Any ticket (if status allows edit) | Own tickets only |
| Add comment | Any ticket (if status allows comments) | Own tickets only |

`created_by` on tickets and comments is **never** accepted in request bodies — it is always derived from the authenticated user.

### Status Changes — Single Enforcement Point

**Ticket status can ONLY be changed via `POST /api/tickets/{id}/status`.**

The generic update endpoint (`PATCH /api/tickets/{id}`) accepts `title`, `description`, `priority`, and `assigned_to` only — it **never** accepts or changes `status`. This gives the state machine exactly one enforcement point in the API layer.

Allowed transitions (enforced in `ticket_status` service):

| From | To |
|------|-----|
| Open | In Progress, Cancelled |
| In Progress | Resolved, Cancelled |
| Resolved | Closed |
| Closed | *(none)* |
| Cancelled | *(none)* |

---

## GET /api/health

### Purpose

Liveness check. Confirms the API is running.

### Request

No body. No query parameters.

```http
GET /api/health
```

### Response

**200 OK**

```json
{
  "status": "ok"
}
```

### Validation Rules

None.

### Error Responses

None expected.

---

## POST /api/auth/login

### Purpose

Authenticate with email and password. Returns a JWT for use on protected endpoints.

### Request

```http
POST /api/auth/login
Content-Type: application/json
```

```json
{
  "email": "alice@example.com",
  "password": "Password123"
}
```

### Response

**200 OK**

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```

### Validation Rules

| Field | Rules |
|-------|-------|
| `email` | Required |
| `password` | Required |

Extra fields are rejected (`422`).

### Error Responses

**401** — invalid email or password:

```json
{
  "error": {
    "code": "unauthorized",
    "message": "Invalid email or password",
    "details": null
  }
}
```

**422** — validation failure.

---

## GET /api/auth/me

### Purpose

Return the currently authenticated user (from JWT).

### Request

```http
GET /api/auth/me
Authorization: Bearer <access_token>
```

### Response

**200 OK**

```json
{
  "id": 1,
  "name": "Alice Admin",
  "email": "alice@example.com",
  "role": "Admin"
}
```

### Error Responses

**401** — missing, invalid, or expired token.

---

## GET /api/users

### Purpose

List all seeded users for the assignee picker. Public (no auth required).

### Request

No body.

```http
GET /api/users
```

### Response

**200 OK**

```json
[
  {
    "id": 1,
    "name": "Alice Admin",
    "email": "alice@example.com",
    "role": "Admin"
  },
  {
    "id": 2,
    "name": "Bob Agent",
    "email": "bob@example.com",
    "role": "Agent"
  }
]
```

`role` is one of: `Admin`, `Agent`, `Manager`, `Requester`.

### Validation Rules

None.

### Error Responses

None expected.

---

## GET /api/tickets

### Purpose

List tickets with optional filters and pagination. Supports the mandatory search/filter capability.

### Request

Query parameters (all optional unless noted):

| Param | Type | Description |
|-------|------|-------------|
| `status` | string | Filter by status enum |
| `priority` | string | Filter by priority enum |
| `q` | string | Case-insensitive substring match on `title` OR `description` |
| `assigned_to` | integer | Filter by assignee user id |
| `created_by` | integer | Filter by creator user id |
| `limit` | integer | Page size (default `50`, min `1`, max `200`) |
| `offset` | integer | Rows to skip (default `0`, min `0`) |

Filters combine with **AND** logic.

```http
GET /api/tickets?status=Open&priority=High&q=login&limit=20&offset=0
```

### Response

**200 OK**

```json
{
  "items": [
    {
      "id": 1,
      "title": "Cannot login to portal",
      "description": "User reports 401 after password reset",
      "priority": "High",
      "status": "Open",
      "assigned_to": 2,
      "created_by": 4,
      "created_at": "2026-07-19T10:00:00+00:00",
      "updated_at": "2026-07-19T10:00:00+00:00",
      "creator": {
        "id": 4,
        "name": "Dana Requester",
        "email": "dana@example.com"
      },
      "assignee": {
        "id": 2,
        "name": "Bob Agent",
        "email": "bob@example.com"
      }
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

Results ordered by `updated_at` descending.

### Validation Rules

- `status` must be one of: `Open`, `In Progress`, `Resolved`, `Closed`, `Cancelled`.
- `priority` must be one of: `Low`, `Medium`, `High`.
- `limit` ∈ [1, 200]; `offset` ≥ 0.

### Error Responses

**422** — invalid enum value or out-of-range `limit`/`offset`:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Request validation failed",
    "details": [
      {
        "type": "enum",
        "loc": ["query", "status"],
        "msg": "Input should be 'Open', 'In Progress', ...",
        "input": "Done"
      }
    ]
  }
}
```

---

## POST /api/tickets

### Purpose

Create a new ticket. Always starts in **Open** status. **`created_by` is set server-side from the JWT** — do not send it in the body.

### Request

```http
POST /api/tickets
Authorization: Bearer <access_token>
Content-Type: application/json
```

```json
{
  "title": "Cannot login to portal",
  "description": "User reports 401 after password reset",
  "priority": "High",
  "assigned_to": 2
}
```

`assigned_to` is optional; omit or set `null` for unassigned.

### Response

**201 Created**

```json
{
  "id": 13,
  "title": "Cannot login to portal",
  "description": "User reports 401 after password reset",
  "priority": "High",
  "status": "Open",
  "assigned_to": 2,
  "created_by": 4,
  "created_at": "2026-07-19T14:30:00+00:00",
  "updated_at": "2026-07-19T14:30:00+00:00",
  "creator": { "id": 4, "name": "Dana Requester", "email": "dana@example.com" },
  "assignee": { "id": 2, "name": "Bob Agent", "email": "bob@example.com" }
}
```

### Validation Rules

| Field | Rules |
|-------|-------|
| `title` | Required; 3–120 characters |
| `description` | Optional; default `""`; max 5000 characters |
| `priority` | Required; `Low`, `Medium`, or `High` |
| `assigned_to` | Optional; if provided, must reference an existing user |

`status` and `created_by` are **not accepted** on create — status defaults to `Open`; `created_by` comes from the authenticated user.

### Error Responses

**401** — missing or invalid JWT.

**422** — validation failure (short title, invalid priority, unknown fields such as `created_by`):

```json
{
  "error": {
    "code": "validation_error",
    "message": "Request validation failed",
    "details": [
      {
        "type": "string_too_short",
        "loc": ["body", "title"],
        "msg": "String should have at least 3 characters",
        "input": "ab"
      }
    ]
  }
}
```

**404** — `assigned_to` references a non-existent user:

```json
{
  "error": {
    "code": "not_found",
    "message": "User not found",
    "details": { "resource": "User", "id": 999 }
  }
}
```

---

## GET /api/tickets/export

### Purpose

Download a CSV of all tickets **created by the authenticated user**. Includes tickets in all statuses. **Must be registered before `GET /api/tickets/{id}`** so `export` is not parsed as a ticket id.

### Request

```http
GET /api/tickets/export
Authorization: Bearer <access_token>
```

No query parameters. Scope is always the JWT subject — `created_by` is not accepted (prevents exporting another user's tickets).

### Response

**200 OK**

```
Content-Type: text/csv; charset=utf-8
Content-Disposition: attachment; filename="tickets_user_4.csv"
```

```csv
id,title,description,priority,status,assigned_to,assignee_name,created_by,creator_name,created_at,updated_at
1,Cannot login,User reports 401,High,Open,2,Bob Agent,4,Dana Requester,2026-07-19T10:00:00+00:00,2026-07-19T10:00:00+00:00
```

If the user has no tickets, returns a CSV with the header row only.

### Validation Rules

- Valid JWT required.
- Export includes only tickets where `created_by` equals the authenticated user's id.

### Error Responses

**401** — missing or invalid JWT.

---

## GET /api/tickets/{id}

### Purpose

Retrieve a single ticket with creator and assignee details.

### Request

```http
GET /api/tickets/1
```

### Response

**200 OK** — same ticket object shape as list items.

### Validation Rules

- `id` must be a valid integer.

### Error Responses

**404** — ticket not found:

```json
{
  "error": {
    "code": "not_found",
    "message": "Ticket not found",
    "details": { "resource": "Ticket", "id": 999 }
  }
}
```

---

## PATCH /api/tickets/{id}

### Purpose

Update ticket fields. Allowed **only** when status is **Open** or **In Progress**. Does **not** accept or change `status` — use the dedicated status endpoint instead. Requires JWT.

### Request

Partial update — include only fields to change.

```http
PATCH /api/tickets/1
Authorization: Bearer <access_token>
Content-Type: application/json
```

```json
{
  "title": "Updated title",
  "priority": "Medium",
  "assigned_to": null
}
```

Accepted fields: `title`, `description`, `priority`, `assigned_to` only.

### Response

**200 OK** — updated ticket object.

### Validation Rules

| Field | Rules |
|-------|-------|
| `title` | If provided: 3–120 characters |
| `description` | If provided: max 5000 characters |
| `priority` | If provided: `Low`, `Medium`, or `High` |
| `assigned_to` | If provided: existing user id, or `null` to clear assignee |

| Business rule | Enforcement |
|---------------|-------------|
| Ticket must exist | 404 |
| Status must be `Open` or `In Progress` | 409 |
| Requester may only edit own tickets | 403 |
| `status` field in body | Rejected — `422` (`extra=forbid`) |
| `assigned_to` user must exist (when non-null) | 404 |

### Error Responses

**401** — missing or invalid JWT.

**403** — requester editing another user's ticket.

**422** — field validation failure.

**404** — ticket or assignee user not found.

**409** — ticket not editable (Resolved, Closed, or Cancelled):

```json
{
  "error": {
    "code": "ticket_not_editable",
    "message": "Ticket cannot be edited in 'Resolved' status.",
    "details": { "status": "Resolved" }
  }
}
```

---

## POST /api/tickets/{id}/status

### Purpose

Change ticket status via the state machine. **This is the ONLY endpoint that may change `status`.** Requires JWT. Only **Admin**, **Agent**, and **Manager** roles may call this endpoint.

### Request

```http
POST /api/tickets/1/status
Authorization: Bearer <access_token>
Content-Type: application/json
```

```json
{
  "status": "In Progress"
}
```

### Response

**200 OK** — updated ticket object with new `status` and refreshed `updated_at`.

### Validation Rules

| Field | Rules |
|-------|-------|
| `status` | Required; must be a valid status enum string |

| Business rule | Enforcement |
|---------------|-------------|
| Ticket must exist | 404 |
| Caller must be Admin, Agent, or Manager | 403 |
| Transition must be allowed from current status | 409 |

### Error Responses

**401** — missing or invalid JWT.

**403** — requester (or other forbidden role) attempting status change.

**422** — invalid or missing `status` value (e.g. `"Done"`):

```json
{
  "error": {
    "code": "validation_error",
    "message": "Request validation failed",
    "details": [
      {
        "type": "enum",
        "loc": ["body", "status"],
        "msg": "Input should be 'Open', 'In Progress', ...",
        "input": "Done"
      }
    ]
  }
}
```

**404** — ticket not found.

**409** — invalid transition:

```json
{
  "error": {
    "code": "invalid_transition",
    "message": "Cannot transition from 'Open' to 'Resolved'. Allowed transitions: In Progress, Cancelled.",
    "details": {
      "current_status": "Open",
      "target_status": "Resolved",
      "allowed": ["In Progress", "Cancelled"]
    }
  }
}
```

---

## GET /api/tickets/{id}/comments

### Purpose

List all comments on a ticket, ordered by `created_at` ascending.

### Request

```http
GET /api/tickets/1/comments
```

### Response

**200 OK**

```json
[
  {
    "id": 1,
    "ticket_id": 1,
    "message": "Investigating the auth logs now.",
    "created_by": 2,
    "created_at": "2026-07-19T11:00:00+00:00",
    "author": {
      "id": 2,
      "name": "Bob Agent",
      "email": "bob@example.com"
    }
  }
]
```

### Validation Rules

- Parent ticket must exist.

### Error Responses

**404** — ticket not found.

---

## POST /api/tickets/{id}/comments

### Purpose

Add a comment to a ticket. Allowed when ticket status is **Open**, **In Progress**, or **Resolved**. Rejected when **Closed** or **Cancelled**. Requires JWT. **`created_by` is set server-side from the JWT.**

### Request

```http
POST /api/tickets/1/comments
Authorization: Bearer <access_token>
Content-Type: application/json
```

```json
{
  "message": "Investigating the auth logs now."
}
```

### Response

**201 Created**

```json
{
  "id": 9,
  "ticket_id": 1,
  "message": "Investigating the auth logs now.",
  "created_by": 2,
  "created_at": "2026-07-19T11:00:00+00:00",
  "author": {
    "id": 2,
    "name": "Bob Agent",
    "email": "bob@example.com"
  }
}
```

### Validation Rules

| Field | Rules |
|-------|-------|
| `message` | Required; 1–2000 characters |

| Business rule | Enforcement |
|---------------|-------------|
| Ticket must exist | 404 |
| Ticket status must be Open, In Progress, or Resolved | 409 |
| Requester may only comment on own tickets | 403 |

### Error Responses

**401** — missing or invalid JWT.

**403** — requester commenting on another user's ticket.

**422** — empty/whitespace message, message too long, or unknown fields such as `created_by`.

**404** — ticket not found.

**409** — comment on Closed or Cancelled ticket:

```json
{
  "error": {
    "code": "comment_not_allowed",
    "message": "Comments are not allowed on tickets in 'Closed' status.",
    "details": { "status": "Closed" }
  }
}
```

---

## Enum Reference

| Field | Values |
|-------|--------|
| `priority` | `Low`, `Medium`, `High` |
| `status` | `Open`, `In Progress`, `Resolved`, `Closed`, `Cancelled` |
| `role` | `Admin`, `Agent`, `Manager`, `Requester` |
