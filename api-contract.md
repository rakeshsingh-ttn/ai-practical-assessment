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
| **422** | Request body or query params fail schema validation (missing fields, wrong types, out-of-range lengths, invalid enum strings) | `validation_error` |
| **404** | Referenced resource does not exist (ticket, user) | `not_found` |
| **409** | Business-rule conflict — valid JSON but operation not allowed | `invalid_transition`, `ticket_not_editable`, `comment_not_allowed` |

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

## GET /api/users

### Purpose

List all seeded users for the "acting as" dropdown and assignee picker.

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

Create a new ticket. Always starts in **Open** status.

### Request

```http
POST /api/tickets
Content-Type: application/json
```

```json
{
  "title": "Cannot login to portal",
  "description": "User reports 401 after password reset",
  "priority": "High",
  "created_by": 4,
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
| `created_by` | Required; must reference an existing user |
| `assigned_to` | Optional; if provided, must reference an existing user |

`status` is **not accepted** on create — always defaults to `Open`.

### Error Responses

**422** — validation failure (short title, invalid priority, missing `created_by`):

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

**404** — `created_by` or `assigned_to` references a non-existent user:

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

Download a CSV of all tickets created by a given user (`created_by`). Includes tickets in all statuses. **Must be registered before `GET /api/tickets/{id}`** so `export` is not parsed as a ticket id.

### Request

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `created_by` | integer | Yes | Creator user id |

```http
GET /api/tickets/export?created_by=4
```

### Response

**200 OK**

```
Content-Type: text/csv
Content-Disposition: attachment; filename="tickets_user_4.csv"
```

```csv
id,title,description,priority,status,assigned_to,assignee_name,created_by,creator_name,created_at,updated_at
1,Cannot login,User reports 401,High,Open,2,Bob Agent,4,Dana Requester,2026-07-19T10:00:00+00:00,2026-07-19T10:00:00+00:00
```

If the user has no tickets, returns a CSV with the header row only.

### Validation Rules

- `created_by` is required.
- `created_by` must reference an existing user.

### Error Responses

**422** — missing `created_by` query parameter.

**404** — user not found:

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

Update ticket fields. Allowed **only** when status is **Open** or **In Progress**. Does **not** accept or change `status` — use the dedicated status endpoint instead.

### Request

Partial update — include only fields to change.

```http
PATCH /api/tickets/1
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
| `status` field in body | Not in schema — ignored if sent |
| `assigned_to` user must exist (when non-null) | 404 |

### Error Responses

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

Change ticket status via the state machine. **This is the ONLY endpoint that may change `status`.** All transitions are validated by `ticket_status.transition()`.

### Request

```http
POST /api/tickets/1/status
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
| Transition must be allowed from current status | 409 |

### Error Responses

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

Add a comment to a ticket. Allowed when ticket status is **Open**, **In Progress**, or **Resolved**. Rejected when **Closed** or **Cancelled**.

### Request

```http
POST /api/tickets/1/comments
Content-Type: application/json
```

```json
{
  "message": "Investigating the auth logs now.",
  "created_by": 2
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
| `created_by` | Required; must reference an existing user |

| Business rule | Enforcement |
|---------------|-------------|
| Ticket must exist | 404 |
| Ticket status must be Open, In Progress, or Resolved | 409 |
| `created_by` user must exist | 404 |

### Error Responses

**422** — empty/whitespace message or message too long.

**404** — ticket or `created_by` user not found.

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
