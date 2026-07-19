# Design

---

# Chat 4 — Data model + API contract
_Exported on 7/19/2026 at 21:20:00 GMT+5:30 from Cursor (3.12.17)_

---

**User**

Using @requirements-analysis.md, design the relational schema for SQLite
(SQLAlchemy 2.0 models will follow it). Requirements:
- users, tickets, comments tables; singular model names in code
- status and priority as constrained strings (CHECK constraints) matching the
  fixed enums
- foreign keys: tickets.assigned_to -> users.id (nullable),
  tickets.created_by -> users.id, comments.ticket_id -> tickets.id,
  comments.created_by -> users.id
- server-managed created_at / updated_at
- indexes that match how we query: tickets(status), tickets(priority),
  tickets(created_by), comments(ticket_id)

Write data-model.md with: an entity-relationship overview, each table with
columns/types/constraints, index rationale, and a short note on why SQLite
(zero-setup for the reviewer) and how it would move to Postgres.

---

**Cursor**

Wrote `data-model.md` with:
- Mermaid ER diagram and relationship table
- `users`, `tickets`, `comments` table definitions with CHECK constraints on enums
- Index rationale for `ix_tickets_status`, `ix_tickets_priority`, `ix_tickets_created_by`, `ix_comments_ticket_id`
- SQLite vs Postgres migration notes

---

**User**

Now write api-contract.md for this API. Endpoints:

- GET    /api/health
- GET    /api/users                          (for dropdowns)
- GET    /api/tickets                        (filters: status, priority, q
                                              [substring over title+description],
                                              assigned_to, created_by;
                                              limit/offset)
- POST   /api/tickets
- GET    /api/tickets/{id}
- PATCH  /api/tickets/{id}                   (title, description, priority,
                                              assigned_to ONLY — never status;
                                              allowed only in Open/In Progress)
- POST   /api/tickets/{id}/status            (body: {"status": "..."} —
                                              the ONLY way to change status)
- GET    /api/tickets/{id}/comments
- POST   /api/tickets/{id}/comments          (rejected on Closed/Cancelled)
- GET    /api/tickets/export?created_by={id} (CSV download, all ticket fields)

For each endpoint use the template: Purpose, Request (JSON example),
Response (JSON example + status code), Validation Rules, Error Responses.
Document the single error shape {"error": {"code", "message", "details"}} once
at the top, and which situations produce 422 vs 404 vs 409. State explicitly
that a separate status endpoint exists so the state machine has exactly one
enforcement point.

---

**Cursor**

Wrote `api-contract.md` with:
- Unified error shape and HTTP code policy (422/404/409) at the top
- Explicit statement that `POST /api/tickets/{id}/status` is the only status change endpoint
- All 11 endpoints documented with Purpose, Request, Response, Validation Rules, Error Responses
- Enum reference appendix

---

**User**

commit and export

---

**Cursor**

Committed `data-model.md`, `api-contract.md`, and appended this Chat 4 session to `ai-prompts/design.md`.

---

# Chat 5 — Design notes, UI flow, test strategy
_Exported on 7/19/2026 at 21:22:00 GMT+5:30 from Cursor (3.12.17)_

---

**User**

Using @requirements-analysis.md @api-contract.md @data-model.md, write three
artifacts:

1. design-notes.md — Architecture Overview, Frontend Design, Backend Design,
   Database Design, Validation Strategy, Error Handling Strategy, Testing Strategy Link
2. ui-flow.md — Ticket List, Ticket Detail, Create Ticket flows with error states
3. test-strategy.md — Test Scope, Unit Tests, API/Integration Tests, Edge Case Tests,
   Tests Not Covered

---

**Cursor**

Wrote all three artifacts:

- **design-notes.md** — React → FastAPI → SQLite architecture, layering, state machine isolation, validation/error handling strategies, link to test-strategy.md
- **ui-flow.md** — Three screens with ASCII layouts, user flows, status button rules, edit/comment availability by status, error state summary (422 inline vs 409/404 banner)
- **test-strategy.md** — Unit/integration scope mapped to existing tests, edge case coverage matrix from requirements-analysis.md, gaps noted, manual smoke checklist

---

**User**

yes please (commit and export)

---

**Cursor**

Committed `design-notes.md`, `ui-flow.md`, `test-strategy.md`, and appended this Chat 5 session to `ai-prompts/design.md`.

