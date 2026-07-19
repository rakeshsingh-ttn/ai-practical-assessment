# Requirement Analysis

## Selected Project Option

**Support Ticket Management System** (backend-heavy option) — a small internal app for creating, updating, commenting on, searching, and progressing support tickets through a defined lifecycle. Stack: Python FastAPI + SQLAlchemy 2.0 + Alembic + SQLite (swappable to Postgres), React (Vite) frontend, pytest for tests. Solo effort (~3 days), no auth, no user-management UI.

## My Understanding (in your own words — write this in plain first person)

I'm building an internal support ticket app where seeded users stand in for real accounts — there's no login, just an "acting as" dropdown in the UI. When I create a ticket or add a comment, the selected user becomes `createdBy`. When I export CSV, I get every ticket I (as that user) created.

Tickets follow a strict lifecycle: Open → In Progress → Resolved → Closed, with Cancelled as an alternate exit from Open or In Progress. The backend enforces this — I can't skip steps, go backwards, or change status through a generic update. I can edit title, description, priority, and assignee only while a ticket is Open or In Progress. Once Resolved, I can still comment but not edit fields. Closed and Cancelled tickets are fully read-only.

I need search (case-insensitive substring on title and description) plus filters by status and priority. Data must persist across restarts. The backend rejects bad input; the UI shows meaningful errors. There's no delete — Cancelled means "we're not doing this."

## Functional Requirements

**FR-1 — Acting-as user context**  
The UI provides a dropdown of seeded users. `createdBy` on new tickets and comments is set from the selected user. No authentication or user-management UI.

**FR-2 — Create ticket**  
Create a ticket with title, description, priority, optional assignee, and `createdBy` (from acting-as selection). New tickets always start in **Open** status.

**FR-3 — List tickets**  
View all tickets from the database in a list (id, title, priority, status, assignee, creator). Support limit/offset pagination with sensible defaults.

**FR-4 — View ticket detail**  
Open a single ticket and see all fields, comment thread, and status-appropriate actions.

**FR-5 — Update ticket fields**  
Update title, description, priority, and assignee via a dedicated update endpoint. Allowed **only** when status is **Open** or **In Progress**. Status is never accepted on this endpoint.

**FR-6 — Status changes via state machine**  
Status changes happen **only** through `POST /api/tickets/{id}/status`. Allowed transitions:

| From | To |
|------|-----|
| Open | In Progress, Cancelled |
| In Progress | Resolved, Cancelled |
| Resolved | Closed |
| Closed | *(none)* |
| Cancelled | *(none)* |

All other transitions are rejected by the backend (HTTP 409).

**FR-7 — Add comments**  
Add comments on **Open**, **In Progress**, and **Resolved** tickets. Comments on **Closed** or **Cancelled** tickets are rejected (HTTP 409).

**FR-8 — Search and filter**  
Case-insensitive substring search on title and description (`q`), plus filter by status and priority. Satisfies the mandatory "one working search or filter" requirement.

**FR-9 — CSV export**  
Export all tickets where `createdBy` equals the currently selected acting-as user. CSV includes all ticket fields.

**FR-10 — Data persistence**  
All data stored in SQLite (swappable to Postgres). Data survives application restart.

**FR-11 — Backend validation**  
Reject invalid input at the API boundary and enforce business rules in services (user exists, edit allowed, comment allowed, valid transitions).

**FR-12 — Meaningful UI errors**  
Surface validation errors inline (422) and other API failures via banner/toast, including clear messages for rejected transitions (409).

**FR-13 — No delete**  
No delete operation. **Cancelled** is the terminal "not doing this" state; **Closed** is the terminal "done" state.

## Non-Functional Requirements

**NFR-1 — Stack**  
Python, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, SQLite. React, Vite. pytest + httpx TestClient.

**NFR-2 — Consistent error shape**  
All API errors: `{"error": {"code", "message", "details"}}`. HTTP 422 (validation), 404 (not found), 409 (business-rule conflict).

**NFR-3 — Layered backend**  
Thin routers; business logic in services. State machine isolated in a dedicated module with a single enforcement point.

**NFR-4 — Mandatory state-machine tests**  
Integration tests prove every valid transition succeeds and invalid transitions are rejected, including from terminal states.

**NFR-5 — Server-managed timestamps**  
`createdAt` on insert; `updatedAt` on any ticket change. Clients cannot set or override.

**NFR-6 — Reviewability**  
AI-assisted code must be reviewed and understood. Prefer small, reviewable changes.

**NFR-7 — Known concurrency limitation**  
Single-user usage; no optimistic locking. Last-write-wins on concurrent edits is acceptable.

## Assumptions

1. **Acting-as user** replaces authentication; `createdBy` and CSV export scope follow the selected user.
2. **Priority** is a fixed enum: Low, Medium, High.
3. **Status** is a fixed enum: Open, In Progress, Resolved, Closed, Cancelled.
4. **Field editing** is allowed only in Open and In Progress; Resolved, Closed, and Cancelled are read-only for fields.
5. **Comments** are allowed on Open, In Progress, and Resolved; rejected (409) on Closed and Cancelled.
6. **Assignee** is optional at creation; if provided, must reference an existing seeded user.
7. **Search/filter** is case-insensitive substring on title + description, combined with status and priority filters (AND logic).
8. **No delete** — Cancelled is the terminal abandonment state.
9. **Pagination** uses limit/offset with sensible defaults; not a UX priority.
10. **Concurrency** — single-user is fine; no optimistic locking (documented limitation).

## Clarifications

| # | Question | Answer |
|---|----------|--------|
| 1 | Without auth, how is `createdBy` determined and what does "self-created" mean for CSV export? | UI has an "acting as" dropdown of seeded users. `createdBy` is set from that selection. "Self-created tickets" for CSV export means tickets where `createdBy` equals the currently selected user. |
| 2 | What are the allowed priority and status values? | Priority: Low, Medium, High. Status: Open, In Progress, Resolved, Closed, Cancelled. Both are fixed enums — no free-text. |
| 3 | When can ticket fields (title, description, priority, assignee) be edited? | Only while status is Open or In Progress. Closed and Cancelled tickets are read-only. (Resolved is also read-only for fields — comments only.) |
| 4 | On which statuses can comments be added? | Open, In Progress, and Resolved — allowed. Closed and Cancelled — rejected with 409. |
| 5 | Is assignee required at creation? | Optional. If provided, must reference an existing seeded user. |
| 6 | What counts as the mandatory search/filter capability? | Case-insensitive substring match on title and description, plus filter by status and priority. |
| 7 | Is there a delete operation? | No. Cancelled is the terminal "not doing this" state. |
| 8 | Is pagination required for the ticket list? | Simple limit/offset with sensible defaults; not a priority for polish. |
| 9 | Who manages timestamps? | Server-managed: `createdAt` on insert, `updatedAt` on any change. |
| 10 | What are concurrency expectations? | Single-user concurrency is fine; no optimistic locking needed (note as known limitation). |
| 11 | Can comments be edited or deleted? | Not specified — assume append-only (no edit/delete of comments). |
| 12 | What validation limits apply to fields? | Not specified by PO — assume title 3–120 chars (required), description up to 5000 chars, comment message 1–2000 chars (required). |
| 13 | Should the UI show only valid status transitions? | Implied by spec — status buttons offer only transitions valid from the current status. |
| 14 | Must data survive server restart? | Yes — SQLite on disk (core requirement from spec). |

## Edge Cases

### State machine

- **Skip-ahead** (Open → Resolved, Open → Closed) → 409 with allowed targets listed.
- **Backward** (In Progress → Open, Resolved → In Progress) → 409.
- **Reopen attempts** (Closed → Open, Cancelled → Open, or any exit from a terminal state) → 409.
- **Resolved → Cancelled** → 409; once Resolved, the only forward path is Closed.
- **From terminal states** (Closed → anything, Cancelled → anything) → 409.
- **Same-status no-op** (Open → Open) → 409.
- **Unknown status string** in the status endpoint body (e.g. `"Done"`) → 422, not 409.
- **Status via PATCH** must not change status; only the dedicated status endpoint may.
- **Resolved tickets** accept comments but reject field edits (409).

### Validation

- Title too short (< 3 chars) or missing → 422.
- Title > 120 chars, description > 5000 chars, comment > 2000 chars → 422.
- Invalid priority or status enum value → 422.
- Non-existent `created_by`, `assigned_to`, or ticket id → 404.
- PATCH on Closed, Cancelled, or Resolved ticket → 409 (`TicketNotEditableError`).
- **Clearing assignee** — PATCH with `assigned_to: null` on an Open/In Progress ticket should unassign (not leave stale assignee).

### Comments

- Comment submitted after ticket was Closed/Cancelled elsewhere → 409 (stale UI).
- **Closing does not delete comments** — existing thread remains visible; only new comments are blocked.
- **Comment on Resolved, then ticket Closed** — prior comments stay; add form must disable or fail on submit.
- **`created_by` on comment must exist** → 404.
- **Whitespace-only message** (e.g. `"   "`) → 422; must contain non-whitespace content.
- Comments are append-only.

### CSV export

- **Scope is creator only** — tickets assigned to the user but created by someone else are excluded.
- **All statuses included** — self-created Cancelled and Closed tickets appear in the export.
- `created_by` user does not exist → 404.
- **Missing `created_by` query parameter** → 422.
- User with zero tickets → CSV with header row only.
- Special characters (commas, quotes, newlines) in title/description must be properly quoted in CSV.
- Export route must be registered before `GET /api/tickets/{id}` to avoid `export` being parsed as an id.

### Search and filter

- Empty `q` → no text filter applied.
- Status + priority + search combine with AND logic.

### UI / acting-as

- No user selected → disable create/comment or prompt selection.
- Changing acting-as user does not retroactively change existing tickets.

### Concurrency (known limitation)

- **Edit after status change** — if another request moves the ticket to Resolved/Closed/Cancelled first, a concurrent PATCH returns 409 instead of applying stale edits.
- **Status race** — two simultaneous transitions: last write wins; no guarantee the intermediate state was observed.
- Simultaneous field edits → last-write-wins; no version column or conflict detection.
