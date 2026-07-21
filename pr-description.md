# Pull Request: Support Ticket Management System

## Summary

This PR delivers a full-stack support ticket app: FastAPI + SQLite backend with an enforced status state machine, React (Vite) frontend with JWT login and role-based UI, Alembic migrations, seed data, and automated plus manual test evidence. I treated the assessment as a real delivery — spec and API contract first, then implementation, then test hardening, JWT auth stretch, and a structured code review with one commit per accepted finding.

---

## Features Implemented (Core acceptance criteria)

| Criterion | What I shipped |
|-----------|----------------|
| **Create via UI** | Create form (login required); `created_by` from JWT; new tickets start **Open** |
| **View all tickets from DB** | List table with id, title, priority, status, assignee, creator (persisted data, not hardcoded) |
| **Detail view** | Ticket fields, comment thread, role-aware status-appropriate actions |
| **Update fields and reassign** | PATCH on **Open** / **In Progress** only; blocked on Resolved/Closed/Cancelled (409); Requesters limited to own tickets |
| **Add comments** | On Open, In Progress, Resolved; author + timestamp; blocked on Closed/Cancelled |
| **Status only via valid transitions** | `POST /api/tickets/{id}/status` only; invalid moves → 409; Admin/Agent/Manager only |
| **Data survives restart** | SQLite persistence; verified in pre-auth Swagger smoke + post-JWT API smoke |
| **Backend validation** | 422/404/409 for bad input, missing users, read-only edits, invalid transitions |
| **CSV export** | `GET /api/tickets/export` (JWT required) — scoped to authenticated user, all statuses |
| **State-machine integration tests** | Parametrized valid/invalid transitions including terminal states |
| **No secrets in repo** | `.env.example` only; `.gitignore` covers `.env`, `*.db`, `venv/`, `node_modules/` |
| **Search and filter** | Case-insensitive `q` on title/description; status + priority filters (AND logic) |
| **JWT login and role-based UI** | `LoginPage` + `UserContext`; drives create, comment, export; status buttons by role |
| **No delete** | No DELETE endpoint or UI; Cancelled/Closed are terminal |

All Core checkboxes in `acceptance-criteria.md` are ticked with evidence in `test-results.md`.

---

## Technical Changes

### State machine (`src/backend/app/services/ticket_status.py`)

- `ALLOWED_TRANSITIONS`, `can_transition()`, `transition()` — single enforcement point for status changes
- Routers never mutate `status` on PATCH; frontend mirrors allowed next states in `constants.js` (backend 409 is the backstop)

### Error handling (`src/backend/app/error_handlers.py`)

- Consistent shape: `{"error": {"code", "message", "details"}}`
- 422 validation, 404 `not_found`, 409 business conflicts (`invalid_transition`, `ticket_not_editable`, `comment_not_allowed`)
- Global 500 handler for unhandled exceptions; `IntegrityError` → 409

### Service layer (`src/backend/app/services/ticket_service.py`)

- CRUD, search/filter, comments, batched CSV export
- Row locking (`with_for_update`) on edit/status/comment mutations
- CSV formula-injection sanitization; LIKE wildcard escaping on search

### API schemas (`src/backend/app/schemas/__init__.py`)

- Request validation with `extra="forbid"`; whitespace-stripped titles
- Response serializers normalize timestamps to second precision

### Frontend (`src/frontend/`)

- Login screen; three screens: list (search/filter/export), detail (edit, status actions, comments), create
- `UserContext` for JWT session; inline 422 errors + `ErrorBanner` for 404/409/500

### Auth (`src/backend/app/auth/`)

- bcrypt password hashing; JWT issue/verify; `get_current_user` dependency
- `POST /api/auth/login`, `GET /api/auth/me`
- Role rules: Admin/Agent/Manager change status; Requester edit/comment on own tickets only
- Export and all mutations require Bearer token; reads remain public (documented in `api-contract.md`)

### Migrations & seed

- `001_initial_schema.py` — users, tickets, comments
- `002_check_constraints.py` — CHECK constraints on status, priority, role enums
- `003_user_password_hash.py` — `password_hash` column on users
- `src/backend/seed.py` — 4 users (default password `Password123`), 12 tickets (all statuses), 8 comments (idempotent)

---

## Database Changes

| Migration | Change |
|-----------|--------|
| `001` | `users`, `tickets`, `comments` tables; FKs; indexes on ticket filters and `comments.ticket_id` |
| `002` | CHECK constraints on `tickets.status`, `tickets.priority`, `users.role` |
| `003` | `users.password_hash` for JWT login |

Seed data covers every ticket status and priority for demo and test coverage. See `database/setup-notes.md` and `data-model.md`.

---

## Testing Done

### Automated (`pytest`)

**91 tests** — all green (`venv/bin/python -m pytest -q`):

| Suite | File | Count | Coverage |
|-------|------|-------|----------|
| State machine unit | `tests/test_state_machine_unit.py` | 16 | Full transition matrix; terminal states |
| State machine integration | `tests/test_state_machine_integration.py` | 13 | Lifecycle, skip/backward/reopen/same-status rejects; PATCH cannot change status |
| Ticket API integration | `tests/test_ticket_api.py` | 30 | Validation, 404/409, search/filter, CSV export (formula injection, special-char quoting), timestamp precision, error shape |
| Auth API | `tests/test_auth_api.py` | 19 | Login, `/me`, protected endpoints, export auth |
| Auth permissions | `tests/test_auth_permissions.py` | 13 | Role rules, `created_by` from token, Requester scoping |

### Manual

| Pass | Result | Logged in |
|------|--------|-----------|
| Pre-auth Swagger smoke | **27/27** | `test-results.md` (2026-07-19, superseded for mutations) |
| Pre-auth UI smoke (browser) | **14/14** | `test-results.md` (2026-07-19, superseded by login flow) |
| Post-JWT API smoke | **17/17** | `test-results.md` (2026-07-20, TestClient) |
| Post-JWT UI smoke (manual browser) | **5/5** | `test-results.md` (2026-07-20) |
| Error-state checks (manual browser) | **PASS** | `test-results.md` (validation 422 + auth banner + 409 shape) |
| README dry run (clean copy) | **PASS** | `test-results.md` (pre-JWT; re-run recommended with login) |

Post-review fixes are logged in `review-fixes.md` (19 commits). Smoke-test follow-ups: timestamp normalization + CSV quoting test (`test_csv_export_quotes_commas_quotes_and_newlines`).

---

## AI Usage Summary

I used **Cursor** throughout, with deliberate process rather than one-shot generation:

1. **Requirements** — AI interviewed me as product owner; I answered clarifying questions, then generated and challenged `requirements-analysis.md`.
2. **Design** — Artifacts in dependency order (acceptance criteria → data model → API contract → UI flow → test strategy) with `@file` context.
3. **Implementation** — Agent mode, one bounded task per prompt; project rules for error shape and state machine.
4. **Validation** — I read every diff, ran pytest, Swagger, and UI smoke; ticked `acceptance-criteria.md` only with evidence.
5. **Review** — Dedicated backend review chat (21 findings); triaged with concrete failure scenarios; applied fixes one commit at a time.
6. **Evidence** — Chat exports in `ai-prompts/`; workflow documented in `tool-workflow.md`.

I did not paste secrets or `.env` contents into prompts. Generated code was reviewed and understood before acceptance — see `code-review-notes.md` and `review-fixes.md`.

---

## Known Limitations

- **Public read endpoints** — `GET /api/tickets`, detail, comments, and `GET /api/users` are intentionally unauthenticated for this demo; mutations and export require JWT.
- **No pagination UI** — API supports `limit`/`offset`; list page uses defaults (50).
- **Single-user concurrency** — no optimistic locking UI; backend uses row locks on mutations but I did not test concurrent multi-client scenarios.
- **No ticket delete** — by design; Cancelled is the exit path.
- **SQLite default** — fine for assessment; Postgres swap is documented but not CI-tested.
- **PATCH `status`** — returns **422** (`extra="forbid"`) rather than silently ignoring; documented in `api-contract.md`.

---

## Future Improvements

- Pagination controls and debounced search polish on the list page.
- Optimistic locking or ETag on PATCH for true multi-user editing.
- Postgres CI job + migration smoke on every PR.
- OpenAPI client generation for the frontend to reduce duplicated constants (`ALLOWED_TRANSITIONS`).
- Protect read endpoints if deployed beyond a trusted internal network.
- E2E suite (Playwright) for the full login + UI flow instead of manual smoke only.
