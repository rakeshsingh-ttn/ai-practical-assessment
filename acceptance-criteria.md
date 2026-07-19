# Acceptance Criteria

## Core

- [ ] **Create via UI** — I can create a ticket from the React UI (title, description, priority, optional assignee); `createdBy` comes from the "acting as" user selector; new tickets start in **Open** status.
- [ ] **View all tickets from DB** — The ticket list shows persisted tickets (not hardcoded) with id, title, priority, status, assignee, and creator.
- [ ] **Detail view** — I can open a ticket and see all fields, the comment thread, and actions appropriate to the current status.
- [ ] **Update fields and reassign** — I can edit title, description, priority, and assignee on **Open** and **In Progress** tickets; edits are blocked on **Resolved**, **Closed**, and **Cancelled** tickets.
- [ ] **Add comments** — I can add comments on **Open**, **In Progress**, and **Resolved** tickets; each comment shows author and timestamp.
- [ ] **Status only via valid transitions** — Status changes use only `POST /api/tickets/{id}/status`; allowed transitions succeed; all others are rejected (409).
- [ ] **Data survives restart** — Tickets, comments, and seed data remain after stopping and restarting the backend.
- [ ] **Backend validation prevents invalid records** — The API rejects bad input (short/missing title, invalid enums, non-existent users) before persisting.
- [ ] **CSV export of self-created tickets** — Export downloads a CSV of all tickets where `createdBy` equals the currently selected acting-as user, including all ticket fields (all statuses).
- [ ] **State-machine integration tests pass** — `pytest` proves every valid transition succeeds and invalid transitions (including from **Closed** and **Cancelled**) are rejected.
- [ ] **No secrets in repo** — No `.env`, keys, or credentials committed; only `.env.example` is in version control.
- [ ] **Search and filter** — Case-insensitive substring search on title/description plus filter by status and priority.
- [ ] **Acting-as user selector** — Header dropdown of seeded users drives `createdBy` on creates/comments and CSV export scope.
- [ ] **No delete** — No ticket delete endpoint or UI; **Cancelled** and **Closed** are terminal states.

## Validation

- [ ] **Title required** — Title shorter than 3 characters or missing → **422** with field details.
- [ ] **Title max length** — Title longer than 120 characters → **422**.
- [ ] **Description max length** — Description longer than 5000 characters → **422**.
- [ ] **Priority enum** — Only `Low`, `Medium`, `High`; invalid value → **422**.
- [ ] **Status enum** — Only `Open`, `In Progress`, `Resolved`, `Closed`, `Cancelled` on the status endpoint; unknown string (e.g. `"Done"`) → **422**.
- [ ] **Comment message required** — Empty or whitespace-only message → **422**.
- [ ] **Comment message max length** — Message longer than 2000 characters → **422**.
- [ ] **Assignee must exist** — `assigned_to` referencing a non-existent user → **404**.
- [ ] **Creator must exist** — `created_by` referencing a non-existent user → **404**.
- [ ] **Ticket must exist** — Requests for a non-existent ticket id → **404**.
- [ ] **Status not on PATCH** — `status` in `PATCH /api/tickets/{id}` does not change status.
- [ ] **Clear assignee** — `PATCH` with `assigned_to: null` on an Open/In Progress ticket clears the assignee.
- [ ] **New ticket defaults** — Created tickets always start as **Open**.
- [ ] **Timestamps server-managed** — `createdAt` on insert; `updatedAt` on any ticket change; client cannot override.

## Error Handling

- [ ] **Consistent error shape** — All API errors return `{"error": {"code", "message", "details"}}`.
- [ ] **422 validation** — Boundary validation failures (missing fields, bad lengths, invalid enums) → **422**.
- [ ] **404 not found** — Missing ticket, user, or export `created_by` → **404**.
- [ ] **409 invalid transition** — Disallowed status change → **409** with current status, target, and allowed targets.
- [ ] **409 edit on read-only ticket** — PATCH on **Resolved**, **Closed**, or **Cancelled** → **409**.
- [ ] **409 comment on closed ticket** — POST comment on **Closed** or **Cancelled** → **409**.
- [ ] **UI inline validation errors** — 422 responses show field-level errors on create/edit forms.
- [ ] **UI banner for API failures** — 404, 409, and 500 display a visible banner with the server message.
- [ ] **UI friendly 409 on transition** — Rejected status action shows the server's transition message.
- [ ] **Disabled UI on terminal tickets** — Closed/Cancelled tickets disable edit/comment with an explanation.

## Testing

- [ ] **Unit: transition matrix** — `can_transition` covers every valid/invalid pair; terminal states have no outgoing transitions.
- [ ] **Integration: Open → In Progress** — Valid; returns updated ticket.
- [ ] **Integration: Open → Cancelled** — Valid; returns updated ticket.
- [ ] **Integration: In Progress → Resolved** — Valid; returns updated ticket.
- [ ] **Integration: In Progress → Cancelled** — Valid; returns updated ticket.
- [ ] **Integration: Resolved → Closed** — Valid; returns updated ticket.
- [ ] **Integration: full lifecycle** — Open → In Progress → Resolved → Closed succeeds end-to-end.
- [ ] **Integration: skip transitions rejected** — Open → Resolved, Open → Closed, Resolved → Cancelled → **409**.
- [ ] **Integration: backward transitions rejected** — In Progress → Open, Resolved → In Progress → **409**.
- [ ] **Integration: reopen rejected** — Closed → Open, Cancelled → Open → **409**.
- [ ] **Integration: terminal state transitions rejected** — Every target from **Closed** and **Cancelled** → **409**.
- [ ] **Integration: same-status no-op rejected** — Open → Open → **409**.
- [ ] **Integration: PATCH cannot change status** — Status unchanged after PATCH with `status` field.
- [ ] **Integration: validation tests** — Short title, invalid user id → expected codes.
- [ ] **Integration: comment rules** — Comment on open ticket succeeds; comment on cancelled ticket → **409**.
- [ ] **Integration: search/filter** — `q`, `status`, and `priority` return expected subsets (AND logic).
- [ ] **Integration: CSV export** — Returns `text/csv`; creator-only scope; header row when user has zero tickets.
- [ ] **All tests green** — `pytest -v` passes with zero failures.
- [ ] **Manual smoke: Swagger** — Full lifecycle, invalid transitions, validation failure, comment on cancelled, CSV download verified in `/docs`.

## Documentation

- [ ] **README runs from scratch** — Clone → venv → pip install → migrate → seed → uvicorn → npm install → npm run dev → working app.
- [ ] **Schema/migrations + seed documented** — `database/setup-notes.md` covers DB choice, migrations, seed, and reset.
- [ ] **`.env.example` present** — Committed with variable names (e.g. `DATABASE_URL`); no real values.
- [ ] **No secrets committed** — `.gitignore` excludes `.env`, `*.db`, `venv/`, `node_modules/`.
- [ ] **API contract documented** — `api-contract.md` matches implemented endpoints and error codes.
- [ ] **Assessment artifacts present** — Required root-level `.md` files exist (`requirements-analysis.md`, `acceptance-criteria.md`, etc.).
