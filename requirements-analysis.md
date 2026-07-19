# Requirement Analysis

## Selected Project Option

**Support Ticket Management System** — backend-heavy option. A small internal app for managing support tickets through a defined lifecycle, with a React frontend and a FastAPI backend.

## My Understanding (in your own words — write this in plain first person)

I need to build a ticket management app that internal support staff would use to track work items from creation through resolution. There is no login — instead, the UI lets me pick which seeded user I am "acting as," and that choice drives who gets credit as `createdBy` on new tickets and whose tickets are exported as CSV.

Tickets move through a strict status lifecycle enforced on the backend; I cannot skip steps or reopen closed work. I can edit ticket details and reassign only while a ticket is still active (Open or In Progress). Comments let people discuss a ticket, but once it is Closed or Cancelled the record is read-only except for viewing history.

The backend must validate everything and return clear errors. The frontend must surface those errors so a user knows what went wrong. Data lives in SQLite so it survives server restarts. Search and filter help me find tickets in a growing list. CSV export gives me a download of all tickets I created.

## Functional Requirements

**FR-1 — User context (no auth)**  
The UI provides an "acting as" user selector populated from seeded users. `createdBy` on new tickets and comments is set from the selected user. No authentication or user-management UI.

**FR-2 — Create ticket**  
A user can create a ticket with title, description, priority, optional assignee, and `createdBy` (from acting-as selection). New tickets start in **Open** status.

**FR-3 — List tickets**  
A user can view all tickets from the database in a list showing id, title, priority, status, assignee, and creator. List supports pagination (limit/offset with sensible defaults).

**FR-4 — View ticket detail**  
A user can open a single ticket and see all fields, its comment thread, and available actions based on current status.

**FR-5 — Update ticket fields**  
A user can update title, description, priority, and assignee via a dedicated update operation. Updates are allowed **only** when status is **Open** or **In Progress**. Status is **not** accepted on this endpoint.

**FR-6 — Status changes via state machine**  
Status changes happen **only** through a dedicated status endpoint. Allowed transitions:

| From | To |
|------|-----|
| Open | In Progress, Cancelled |
| In Progress | Resolved, Cancelled |
| Resolved | Closed |
| Closed | *(none)* |
| Cancelled | *(none)* |

All other transitions are rejected by the backend.

**FR-7 — Add comments**  
A user can add comments to a ticket. Comments are allowed on **Open**, **In Progress**, and **Resolved** tickets. Comments on **Closed** or **Cancelled** tickets are rejected.

**FR-8 — Search and filter**  
The ticket list supports case-insensitive substring search on title and description (`q`), plus filter by status and priority. This satisfies the mandatory "one working search or filter" requirement.

**FR-9 — CSV export**  
A user can export all tickets they created (`createdBy` equals the currently selected acting-as user) as a CSV file containing all ticket fields.

**FR-10 — Data persistence**  
All users, tickets, and comments are stored in a database (SQLite, swappable to Postgres). Data survives application restart.

**FR-11 — Backend validation**  
The API rejects invalid input at the boundary (Pydantic) and enforces business rules in services (assignee exists, edit allowed, comment allowed, valid transitions).

**FR-12 — Meaningful UI errors**  
The frontend displays validation errors inline (422) and other API failures via banner/toast, including friendly messages for rejected status transitions (409).

**FR-13 — No delete**  
There is no delete operation. **Cancelled** is the terminal "not doing this" state; **Closed** is the terminal "done" state.

## Non-Functional Requirements

**NFR-1 — Stack**  
Backend: Python, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, SQLite. Frontend: React, Vite. Tests: pytest with httpx TestClient.

**NFR-2 — Consistent error shape**  
All API errors return `{"error": {"code", "message", "details"}}` with appropriate HTTP status codes (422 validation, 404 not found, 409 business-rule conflict).

**NFR-3 — Layered backend**  
Routers stay thin; business logic lives in services. The state machine is an isolated module with a single enforcement point.

**NFR-4 — Testability**  
Integration tests run against the real FastAPI app with a temporary in-memory SQLite database. State-machine tests cover every valid transition and representative invalid ones.

**NFR-5 — Reviewability**  
Code is AI-assisted but must be reviewed and understood by the developer. Small, reviewable changes; no unnecessary frameworks.

**NFR-6 — Timestamps**  
`createdAt` is set on insert; `updatedAt` is refreshed on any ticket change. Both are server-managed.

**NFR-7 — Time budget**  
Solo effort, ~3 days. Core features before stretch goals.

## Assumptions

1. **Acting-as user** replaces authentication; `createdBy` and CSV export scope follow the selected user.
2. **Priority** is a fixed enum: Low, Medium, High.
3. **Status** is a fixed enum: Open, In Progress, Resolved, Closed, Cancelled.
4. **Field editing** is limited to Open and In Progress statuses.
5. **Comments** are allowed on Open, In Progress, and Resolved; rejected on Closed and Cancelled.
6. **Assignee** is optional at creation but must reference an existing seeded user when provided.
7. **Search** is case-insensitive substring match on title and description, combined with status/priority filters.
8. **No delete** — Cancelled and Closed are terminal states.
9. **Pagination** uses limit/offset (default limit 50, max 200); not a primary UX concern.
10. **Concurrency** — single-user usage is fine; no optimistic locking (documented limitation).

## Clarifications

| # | Question | Answer |
|---|----------|--------|
| 1 | Without auth, how is `createdBy` determined and what does "self-created" mean for CSV? | UI has an "acting as" dropdown of seeded users. `createdBy` comes from that selection. CSV export returns tickets where `createdBy` equals the selected user. |
| 2 | What are the allowed priority and status values? | Priority: Low, Medium, High. Status: Open, In Progress, Resolved, Closed, Cancelled. Both are fixed enums. |
| 3 | When can ticket fields be edited? | Only while status is Open or In Progress. Closed and Cancelled tickets are read-only. |
| 4 | When can comments be added? | Open, In Progress, and Resolved — yes. Closed and Cancelled — rejected with 409. |
| 5 | Is assignee required? | Optional at creation. If provided, must reference an existing seeded user. |
| 6 | What counts as the mandatory search/filter? | Case-insensitive substring on title + description, plus filter by status and priority. |
| 7 | Is there a delete operation? | No. Cancelled is the "won't do" terminal state. |
| 8 | Pagination requirements? | Simple limit/offset with sensible defaults; not a priority for UX polish. |
| 9 | Who manages timestamps? | Server sets `createdAt` on insert and `updatedAt` on any change. |
| 10 | Concurrency expectations? | Single-user is fine; no optimistic locking needed (known limitation). |

## Edge Cases

### State machine

- **Skip-ahead transitions** (e.g. Open → Resolved, Open → Closed) must return 409 with a message listing allowed targets.
- **Backward transitions** (e.g. In Progress → Open, Resolved → In Progress) must return 409.
- **Transitions from terminal states** (Closed → anything, Cancelled → anything) must return 409.
- **Same-status "transition"** (e.g. Open → Open) must return 409 — no-op transitions are not allowed.
- **Status via PATCH** must be ignored or rejected; status changes only through `POST /api/tickets/{id}/status`.
- **Resolved is not editable** for field updates (only Open/In Progress) but still accepts comments until Closed.

### Validation

- **Title** required, 3–120 characters; empty or too-short title → 422.
- **Description** optional at creation (defaults to empty), max 5000 characters.
- **Comment message** required, 1–2000 characters.
- **Invalid enum values** for priority or status in request body → 422.
- **Non-existent user** as `createdBy`, `assigned_to`, or comment author → 404.
- **Non-existent ticket** on any ticket-scoped endpoint → 404.
- **PATCH with no fields** (empty body or all nulls) should succeed as a no-op or be rejected consistently — either is acceptable if documented.

### Comments

- Commenting on a ticket that was Closed/Cancelled **after** the detail page loaded should fail with 409 on submit (stale UI).
- Comments are append-only; no edit or delete of comments.

### CSV export

- Export with a `created_by` user id that does not exist → 404.
- User with zero tickets → valid CSV with header row only (or empty file — must be consistent).
- CSV must include all ticket scalar fields and survive special characters in title/description (proper quoting).
- Export route must be registered **before** `GET /api/tickets/{id}` so `export` is not parsed as an id.

### Search and filter

- Empty search string should behave as "no text filter" (return all, subject to other filters).
- Filters combine with AND logic (status AND priority AND search text).
- Search is case-insensitive but does not support regex or full-text ranking.

### UI / acting-as

- If no user is selected in the acting-as dropdown, create and comment actions should be disabled or prompt selection.
- Changing acting-as user does not change existing tickets; it only affects new creates and CSV scope.

### Concurrency (known limitation)

- Two users editing the same ticket simultaneously may produce last-write-wins on fields; no version column or conflict detection.
- A status transition and a field edit in parallel could race; acceptable for this scope.

### Persistence

- Server restart must not lose data (SQLite file on disk, not in-memory for production).
- Seed data is idempotent on re-run; migrations are forward-only.
