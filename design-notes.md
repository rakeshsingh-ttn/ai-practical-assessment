# Design Notes

## Architecture Overview

```
┌─────────────────┐     JSON/HTTP      ┌─────────────────┐     SQLAlchemy     ┌─────────┐
│  React SPA      │  ───────────────>  │  FastAPI API    │  ───────────────>  │ SQLite  │
│  (Vite, :5173)  │  <───────────────  │  (uvicorn:8000) │  <───────────────  │ app.db  │
└─────────────────┘                    └─────────────────┘                    └─────────┘
```

**Stack:** React SPA → FastAPI JSON API → SQLite via SQLAlchemy 2.0. No auth layer; the frontend passes `created_by` from the acting-as user selector.

### Request lifecycle

1. **Browser** — user action triggers a call through `src/frontend/src/api/client.js` (single API client; no `fetch` in components).
2. **Router** — FastAPI router (`routers/tickets.py`, `users.py`, `health.py`) receives the request, parses query/body via Pydantic schemas.
3. **Service** — router delegates to `ticket_service` for business logic (list, create, update, comments, CSV export).
4. **State machine** — status changes route exclusively through `ticket_service.change_ticket_status()` → `ticket_status.transition()`.
5. **Database** — SQLAlchemy session reads/writes models; `commit()` persists changes.
6. **Response** — Pydantic `response_model` serializes the result, or an exception handler returns the standard error shape.

### Where validation lives

| Layer | Responsibility |
|-------|----------------|
| **Pydantic schemas** (`schemas/`) | Field types, lengths, enum membership at the API boundary → **422** |
| **Services** (`services/ticket_service.py`) | User/ticket existence, edit-allowed statuses, comment-allowed statuses → **404** / **409** |
| **State machine** (`services/ticket_status.py`) | Allowed status transitions → **409** (`invalid_transition`) |

### Where the state machine lives

`src/backend/app/services/ticket_status.py` — isolated module with `ALLOWED_TRANSITIONS`, `can_transition()`, and `transition()`. Exposed only via `POST /api/tickets/{id}/status`. See [api-contract.md](api-contract.md).

---

## Frontend Design

### Pages and routing

| Route | Component | Purpose |
|-------|-----------|---------|
| `/` | `TicketListPage` | List, search, filter, export, navigate to detail/create |
| `/tickets/new` | `CreateTicketPage` | Create ticket form |
| `/tickets/:id` | `TicketDetailPage` | View/edit ticket, status actions, comments |

### Components

| Component | Role |
|-----------|------|
| `App.jsx` | Layout, header with acting-as selector, React Router routes |
| `UserContext.jsx` | Loads users on mount; holds `currentUserId` / `currentUser` |
| `ErrorBanner.jsx` | Dismissible banner for non-422 API errors; `FieldError` for inline validation |
| `api/client.js` | Single HTTP module — all endpoints, `ApiError` parsing |

### Acting-as user selector

Rendered in the header (`App.jsx`). Populated from `GET /api/users`. Selection stored in `UserContext` and used as:

- `created_by` on `POST /api/tickets` and `POST /api/tickets/{id}/comments`
- `created_by` query param on CSV export (`GET /api/tickets/export?created_by=...`)

### Status UI

`constants.js` mirrors backend `ALLOWED_TRANSITIONS`. `TicketDetailPage` renders status action buttons **only** for transitions valid from the current status. `EDITABLE_STATUSES` and `COMMENT_ALLOWED_STATUSES` control edit form and comment form visibility.

---

## Backend Design

### Layering

```
routers/          →  HTTP boundary, thin — parse input, call service, return response
  tickets.py
  users.py
  health.py
services/         →  business logic
  ticket_service.py
  ticket_status.py   ← state machine (isolated)
models/           →  SQLAlchemy ORM entities
  entities.py       User, Ticket, Comment
schemas/          →  Pydantic request/response DTOs
```

Routers do not contain business rules. Services do not know about HTTP.

### State machine isolation

`ticket_status.py` defines:

```python
ALLOWED_TRANSITIONS = {
    Open:        {In Progress, Cancelled},
    In Progress: {Resolved, Cancelled},
    Resolved:    {Closed},
    Closed:      {},
    Cancelled:   {},
}
```

`can_transition(current, target) -> bool` — pure function, no DB access.  
`transition(ticket, target)` — applies change or raises `InvalidTransitionError`.

**Why isolate it:**

- **Single enforcement point** — one table, one function; impossible to bypass from PATCH or seed scripts at runtime.
- **Unit testable without HTTP or DB** — full transition matrix tested in `test_state_machine_unit.py`.
- **Integration testable independently** — `test_state_machine_integration.py` proves the HTTP endpoint honours the same rules.
- **Readable** — reviewers can verify allowed transitions in one file.

---

## Database Design

See [data-model.md](data-model.md) for the full ER diagram, table definitions, indexes, and SQLite/Postgres notes.

**Summary:** three tables — `users`, `tickets`, `comments`. Fixed enums enforced via CHECK constraints (and Pydantic/SQLAlchemy enums in code). Foreign keys: `tickets.created_by` → `users.id`, `tickets.assigned_to` → `users.id` (nullable), `comments.ticket_id` → `tickets.id`, `comments.created_by` → `users.id`.

### Migration + seed approach

- **Alembic** migrations in `database/migrations/`; initial migration `001_initial_schema.py` creates all tables and indexes.
- **Seed script** `python -m src.backend.seed` — idempotent insert of 4 users, ~12 tickets (all statuses/priorities), ~8 comments. Seed sets statuses directly (bypasses state machine); runtime changes always go through `transition()`.
- **Reset:** delete `app.db`, re-run `alembic upgrade head` and seed. Documented in `database/setup-notes.md`.

---

## Validation Strategy

### Pydantic at the boundary

Request schemas in `schemas/__init__.py` enforce before service code runs:

| Schema | Key rules |
|--------|-----------|
| `TicketCreate` | title 3–120, description ≤ 5000, priority enum, `created_by` required |
| `TicketUpdate` | optional fields with same length/enum rules; **no `status` field** |
| `TicketStatusUpdate` | `status` enum only |
| `CommentCreate` | message 1–2000, `created_by` required |

Failures → `RequestValidationError` → **422** with Pydantic error list in `details`.

### Service-level business rules

| Rule | Service check | Code |
|------|---------------|------|
| User exists | `get_user_or_404()` | **404** |
| Ticket exists | `get_ticket_or_404()` | **404** |
| Edit allowed | `ticket.status in EDITABLE_STATUSES` | **409** `ticket_not_editable` |
| Comment allowed | `ticket.status in COMMENT_ALLOWED_STATUSES` | **409** `comment_not_allowed` |
| Valid transition | `transition(ticket, target)` | **409** `invalid_transition` |

---

## Error Handling Strategy

### Backend: exception → handler → JSON

```
AppError subclasses          register_error_handlers()
  NotFoundError        →  404  { code: "not_found", ... }
  InvalidTransitionError → 409  { code: "invalid_transition", ... }
  TicketNotEditableError → 409  { code: "ticket_not_editable", ... }
  CommentNotAllowedError → 409  { code: "comment_not_allowed", ... }
RequestValidationError   →  422  { code: "validation_error", details: [...] }
```

All errors use shape: `{"error": {"code", "message", "details"}}`. See [api-contract.md](api-contract.md).

### HTTP code policy

| Code | Meaning | Frontend handling |
|------|---------|-------------------|
| **422** | Invalid input shape/values | Parse `details` array → inline `FieldError` under the relevant form field |
| **404** | Resource not found | `ErrorBanner` with server `message` |
| **409** | Business rule conflict | `ErrorBanner` with server `message` (transition errors include allowed targets) |
| **500** | Unexpected server error | `ErrorBanner` with generic or server message |

### Frontend rendering

- `api/client.js` throws `ApiError` with `code`, `message`, `details`, `status`.
- `formatApiError(err)` in `ErrorBanner.jsx` produces user-facing text.
- Create/edit forms: 422 → map `details[].loc` to field names → `<FieldError>`.
- Status buttons, comments, list load, export: 409/404/500 → dismissible `<ErrorBanner>` at top of page.

---

## Testing Strategy Link

See [test-strategy.md](test-strategy.md) for full test scope, unit/integration coverage, edge cases, and gaps (no frontend e2e — manual smoke instead).
