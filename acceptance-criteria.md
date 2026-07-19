# Acceptance Criteria

Use this checklist during development and before submission. Tick each box when verified.

## Core

- [ ] **Create via UI** — I can create a ticket from the React UI with title, description, priority, optional assignee; `createdBy` is set from the "acting as" user selector; new ticket starts in **Open** status.
- [ ] **View all tickets from DB** — The ticket list loads all persisted tickets (not hardcoded data) showing id, title, priority, status, assignee, and creator.
- [ ] **Detail view** — I can open a ticket and see all fields, comment thread, and status-appropriate actions.
- [ ] **Update fields and reassign** — I can edit title, description, priority, and assignee on **Open** and **In Progress** tickets; edits are blocked on **Closed**, **Cancelled**, and **Resolved** tickets.
- [ ] **Add comments** — I can add comments on **Open**, **In Progress**, and **Resolved** tickets; the comment appears in the thread with author and timestamp.
- [ ] **Status only via valid transitions** — Status changes happen only through dedicated status actions / `POST /api/tickets/{id}/status`; only transitions allowed by the state machine succeed; all others are rejected.
- [ ] **Data survives restart** — After stopping and restarting the backend, previously created tickets, comments, and seed data are still present.
- [ ] **Backend validation prevents invalid records** — The API rejects bad input (missing/short title, invalid enums, non-existent users) before persisting invalid data.
- [ ] **CSV export of self-created tickets** — "Export my tickets" downloads a CSV of all tickets where `createdBy` matches the currently selected acting-as user, including all ticket fields.
- [ ] **State-machine integration tests pass** — `pytest` suite proves every valid transition succeeds and representative invalid transitions (including from **Closed** and **Cancelled**) are rejected with 409.
- [ ] **No secrets in repo** — No `.env`, API keys, or credentials committed; only `.env.example` is in version control.
- [ ] **Search or filter works** — Ticket list supports case-insensitive substring search on title/description and/or filter by status and priority.
- [ ] **Acting-as user selector** — Header dropdown lists seeded users; selection drives `createdBy` on creates/comments and CSV export scope.
- [ ] **No delete operation** — There is no ticket delete endpoint or UI; **Cancelled** and **Closed** are terminal states.

## Validation

- [ ] **Title required** — Creating or updating with title shorter than 3 characters returns **422** with field-level details.
- [ ] **Title max length** — Title longer than 120 characters is rejected with **422**.
- [ ] **Description max length** — Description longer than 5000 characters is rejected with **422**.
- [ ] **Priority enum** — Only `Low`, `Medium`, `High` accepted; invalid value returns **422**.
- [ ] **Status enum** — Only `Open`, `In Progress`, `Resolved`, `Closed`, `Cancelled` accepted on status endpoint; invalid value returns **422**.
- [ ] **Comment message required** — Empty comment message returns **422**.
- [ ] **Comment message max length** — Comment longer than 2000 characters returns **422**.
- [ ] **Assignee must exist** — `assigned_to` referencing a non-existent user id returns **404**.
- [ ] **Creator must exist** — `created_by` referencing a non-existent user id returns **404**.
- [ ] **Ticket must exist** — Requests for a non-existent ticket id return **404**.
- [ ] **Status not on PATCH** — Sending `status` in `PATCH /api/tickets/{id}` does not change status (field excluded or ignored; only the status endpoint may change it).
- [ ] **New ticket defaults** — Created tickets always start as **Open** regardless of client input.
- [ ] **Timestamps server-managed** — `createdAt` set on insert; `updatedAt` refreshed on ticket changes; client cannot override.

## Error Handling

- [ ] **Consistent error shape** — All API errors return `{"error": {"code", "message", "details"}}`.
- [ ] **422 for validation** — Pydantic / boundary validation failures return **422** with `code` and field details where applicable.
- [ ] **404 for not found** — Missing ticket, user, or comment resource returns **404** with a clear message.
- [ ] **409 for invalid transition** — Disallowed status change returns **409** with message naming current status, target status, and allowed targets.
- [ ] **409 for edit on read-only ticket** — PATCH on **Closed**, **Cancelled**, or **Resolved** ticket returns **409** (`TicketNotEditableError`).
- [ ] **409 for comment on terminal ticket** — POST comment on **Closed** or **Cancelled** ticket returns **409** (`CommentNotAllowedError`).
- [ ] **UI inline validation errors** — Form validation failures (422) show field-level errors inline on create/edit forms.
- [ ] **UI banner for API failures** — Non-422 errors (404, 409, 500) display a visible error banner with the server message.
- [ ] **UI friendly 409 on transition** — Rejected status button action shows the server's transition error message, not a generic failure.
- [ ] **Disabled UI on terminal tickets** — Closed/Cancelled tickets show disabled edit/comment controls with an explanation.

## Testing

- [ ] **Unit: transition matrix** — `can_transition` tested for every valid and invalid pair; terminal states have no outgoing transitions.
- [ ] **Integration: Open → In Progress** — Valid transition returns 200 and updated status.
- [ ] **Integration: Open → Cancelled** — Valid transition returns 200 and updated status.
- [ ] **Integration: In Progress → Resolved** — Valid transition returns 200 and updated status.
- [ ] **Integration: In Progress → Cancelled** — Valid transition returns 200 and updated status.
- [ ] **Integration: Resolved → Closed** — Valid transition returns 200 and updated status.
- [ ] **Integration: full lifecycle** — Open → In Progress → Resolved → Closed succeeds end-to-end.
- [ ] **Integration: skip transitions rejected** — e.g. Open → Resolved, Open → Closed return **409**.
- [ ] **Integration: backward transitions rejected** — e.g. In Progress → Open returns **409**.
- [ ] **Integration: terminal state transitions rejected** — Every target status from **Closed** and **Cancelled** returns **409**.
- [ ] **Integration: PATCH cannot change status** — Attempting status change via PATCH leaves status unchanged.
- [ ] **Integration: validation tests** — Short title, invalid user id, and similar cases return expected codes.
- [ ] **Integration: comment rules** — Comment on cancelled ticket returns **409**; comment on open ticket succeeds.
- [ ] **Integration: search/filter** — `q`, `status`, and `priority` query params return expected subsets.
- [ ] **Integration: CSV export** — Export returns `text/csv` with header row and correct rows for `created_by`.
- [ ] **All tests green** — `pytest -v` passes with zero failures.
- [ ] **Manual smoke: Swagger** — Full lifecycle, invalid transitions, validation failure, comment on cancelled, and CSV download verified in `/docs`.

## Documentation

- [ ] **README runs from scratch** — A new clone can follow README steps (venv, pip install, migration, seed, uvicorn, npm install, npm run dev) and reach a working app.
- [ ] **Schema/migrations documented** — `database/setup-notes.md` explains DB choice, how to run migrations, seed, and reset.
- [ ] **`.env.example` present** — Committed with expected variable names (e.g. `DATABASE_URL`); no real values.
- [ ] **No secrets committed** — `.gitignore` excludes `.env`, `*.db`, `venv/`, `node_modules/`; repo contains no credentials.
- [ ] **API documented** — `api-contract.md` matches implemented endpoints and error codes.
- [ ] **Assessment artifacts present** — `requirements-analysis.md`, `acceptance-criteria.md`, and other required `.md` files exist at repo root.
