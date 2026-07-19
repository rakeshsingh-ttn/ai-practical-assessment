# Data Model

Relational schema for the Support Ticket Management System. SQLAlchemy 2.0 models (`User`, `Ticket`, `Comment`) map to these tables using singular class names and snake_case column names.

## Entity-Relationship Overview

```mermaid
erDiagram
    users ||--o{ tickets : "creates (created_by)"
    users ||--o{ tickets : "assigned (assigned_to)"
    users ||--o{ comments : "authors (created_by)"
    tickets ||--o{ comments : "has"

    users {
        int id PK
        string name
        string email UK
        string role
    }

    tickets {
        int id PK
        string title
        text description
        string priority
        string status
        int assigned_to FK "nullable"
        int created_by FK
        datetime created_at
        datetime updated_at
    }

    comments {
        int id PK
        int ticket_id FK
        text message
        int created_by FK
        datetime created_at
    }
```

**Relationships**

| From | To | Cardinality | FK column | Notes |
|------|-----|-------------|-----------|-------|
| `users` | `tickets` | 1:N | `tickets.created_by` | Required — every ticket has a creator |
| `users` | `tickets` | 1:N | `tickets.assigned_to` | Optional — ticket may be unassigned |
| `tickets` | `comments` | 1:N | `comments.ticket_id` | Append-only comment thread |
| `users` | `comments` | 1:N | `comments.created_by` | Comment author |

No delete operations in the application — terminal ticket states (`Closed`, `Cancelled`) preserve rows and their comments.

---

## Table: `users`

Seeded reference data for the "acting as" user selector. No user-management UI.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | `INTEGER` | `PRIMARY KEY` | Auto-increment |
| `name` | `VARCHAR(100)` | `NOT NULL` | Display name |
| `email` | `VARCHAR(255)` | `NOT NULL`, `UNIQUE` | Unique per user |
| `role` | `VARCHAR(20)` | `NOT NULL`, `CHECK (role IN ('Admin','Agent','Manager','Requester'))` | Fixed enum |

**ORM model:** `User`

---

## Table: `tickets`

Core entity. Status changes are enforced in the application state machine, not by the database.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | `INTEGER` | `PRIMARY KEY` | Auto-increment |
| `title` | `VARCHAR(120)` | `NOT NULL` | 3–120 chars enforced at API layer |
| `description` | `TEXT` | `NOT NULL`, default `''` | Max 5000 chars at API layer |
| `priority` | `VARCHAR(10)` | `NOT NULL`, `CHECK (priority IN ('Low','Medium','High'))` | Fixed enum |
| `status` | `VARCHAR(20)` | `NOT NULL`, `CHECK (status IN ('Open','In Progress','Resolved','Closed','Cancelled'))`, default `'Open'` | Fixed enum; default on insert |
| `assigned_to` | `INTEGER` | `NULL`, `REFERENCES users(id)` | Optional assignee |
| `created_by` | `INTEGER` | `NOT NULL`, `REFERENCES users(id)` | Creator (acting-as user) |
| `created_at` | `DATETIME` | `NOT NULL`, server default `CURRENT_TIMESTAMP` | Set on insert; client cannot override |
| `updated_at` | `DATETIME` | `NOT NULL`, server default `CURRENT_TIMESTAMP` | Refreshed on any ticket change |

**ORM model:** `Ticket`

**Business rules (application layer, not DB):**

- Field edits (`title`, `description`, `priority`, `assigned_to`) allowed only when `status` is `Open` or `In Progress`.
- Status transitions allowed only via `POST /api/tickets/{id}/status` through the state machine service.

---

## Table: `comments`

Append-only discussion thread on a ticket.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | `INTEGER` | `PRIMARY KEY` | Auto-increment |
| `ticket_id` | `INTEGER` | `NOT NULL`, `REFERENCES tickets(id)` | Parent ticket |
| `message` | `TEXT` | `NOT NULL` | 1–2000 chars at API layer |
| `created_by` | `INTEGER` | `NOT NULL`, `REFERENCES users(id)` | Comment author |
| `created_at` | `DATETIME` | `NOT NULL`, server default `CURRENT_TIMESTAMP` | Set on insert |

**ORM model:** `Comment`

No `updated_at` — comments are never edited or deleted.

**Business rules (application layer):**

- Comments allowed when parent ticket `status` is `Open`, `In Progress`, or `Resolved`.
- Rejected (409) when parent is `Closed` or `Cancelled`.

---

## Indexes

| Index | Table | Column(s) | Rationale |
|-------|-------|-----------|-----------|
| `ix_tickets_status` | `tickets` | `status` | List/filter by status (`GET /api/tickets?status=...`) |
| `ix_tickets_priority` | `tickets` | `priority` | List/filter by priority (`GET /api/tickets?priority=...`) |
| `ix_tickets_created_by` | `tickets` | `created_by` | CSV export and filter by creator (`GET /api/tickets/export?created_by=...`, `?created_by=...`) |
| `ix_comments_ticket_id` | `comments` | `ticket_id` | Load comment thread for a ticket (`GET /api/tickets/{id}/comments`) |

**Not indexed (by design):**

- `tickets.title` / `tickets.description` — search uses `LIKE`/`ILIKE` substring match; a full table scan is acceptable at assessment scale. Postgres migration could add `GIN` full-text or `trigram` indexes if needed.
- `users.email` — covered by the `UNIQUE` constraint (implicit index).

**Optional addition:** `ix_tickets_assigned_to` on `tickets(assigned_to)` if filtering by assignee (`?assigned_to=...`) becomes hot; included in the current implementation.

---

## Enum Reference

| Domain | Allowed values |
|--------|----------------|
| `users.role` | `Admin`, `Agent`, `Manager`, `Requester` |
| `tickets.priority` | `Low`, `Medium`, `High` |
| `tickets.status` | `Open`, `In Progress`, `Resolved`, `Closed`, `Cancelled` |

Enforced at three layers: `CHECK` constraints in the database, Pydantic enums at the API boundary, and the state machine service for transitions.

---

## SQLite vs Postgres

### Why SQLite

- **Zero setup** for the reviewer — no database server to install or configure; a single `app.db` file is created by migration.
- **Sufficient for scope** — single-user internal tool with modest data volume; supports foreign keys, indexes, transactions, and `CHECK` constraints.
- **Fast local dev** — `sqlite:///./app.db` in `.env`; tests use in-memory SQLite (`sqlite:///:memory:`).

### Moving to Postgres

The schema is intentionally portable. To switch:

1. Set `DATABASE_URL=postgresql+psycopg2://user:pass@host/dbname` in `.env`.
2. Run the same Alembic migrations — SQLAlchemy abstracts dialect differences.
3. Minor adjustments for production:
   - Use `TIMESTAMPTZ` instead of `DATETIME` for timezone-aware timestamps (already modeled with `DateTime(timezone=True)`).
   - Replace `CHECK`-on-string enums with native Postgres `ENUM` types if preferred (optional; `CHECK` works on both).
   - Add connection pooling (e.g. PgBouncer) and `pool_pre_ping=True` on the engine.
   - Consider `GIN`/`trigram` indexes on `title`/`description` for search at scale.

No application code changes are required beyond the connection string and optional dialect-specific index tuning.
