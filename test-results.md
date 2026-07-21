# Test Results

> **Note:** Sections dated **2026-07-19** cover the pre-JWT (acting-as) build. Post-JWT verification is in the **Post-JWT verification (2026-07-20)** section at the bottom.

## Automated tests

**Date:** 2026-07-19 *(pre-JWT)*  
**Command:** `pytest -v`  
**Result:** **49 passed**, 0 failed

| Suite | File | Tests |
|-------|------|-------|
| State machine unit | `tests/test_state_machine_unit.py` | 16 |
| State machine integration | `tests/test_state_machine_integration.py` | 8 |
| Ticket API | `tests/test_ticket_api.py` | 19 |

---

## Manual Swagger smoke test

**Date:** 2026-07-19  
**Environment:** `uvicorn src.backend.app.main:app --reload --port 8000`  
**UI:** http://localhost:8000/docs  
**Result:** **27/27 checks passed**, 0 failures

### 0. Setup

| Step | Result | Evidence |
|------|--------|----------|
| 0.1 Health | PASS | `{"status":"ok"}` |
| 0.2 Users | PASS | 4 users: Alice Admin, Bob Agent, Carol Manager, Dave Requester |

### 1. List & filter

| Step | Result | Evidence |
|------|--------|----------|
| 1.1 List all | PASS | `total: 12` |
| 1.2 Filter status | PASS | `status=Open` → 3 tickets |
| 1.3 Filter priority | PASS | `priority=High` → 4 tickets |
| 1.4 Search `q` | PASS | `q=vpn` matched "VPN not connecting" (case-insensitive) |
| 1.5 Get by id | PASS | Full ticket with `creator` and `assignee` objects |

### 2. Create + validation

| Step | Result | Evidence |
|------|--------|----------|
| 2.1 Create ticket | PASS | **201**, ticket id **13**, status `Open` |
| 2.2 Short title | PASS | **422** `validation_error`, `min_length 3` on title |
| 2.3 Invalid user | PASS | **404** `not_found` for `created_by: 9999` |

### 3. PATCH rules

| Step | Result | Evidence |
|------|--------|----------|
| 3.1 Update + clear assignee | PASS | Title updated; `assigned_to: null` cleared assignee |
| 3.2 PATCH Closed ticket | PASS | Ticket 4 → **409** `ticket_not_editable` |
| 3.3 Status not via PATCH | PASS | Status unchanged after PATCH |

### 4. Valid lifecycle (ticket 13)

| Step | Result | Evidence |
|------|--------|----------|
| 4.1 Open → In Progress | PASS | **200** |
| 4.2 In Progress → Resolved | PASS | **200** |
| 4.3 Resolved → Closed | PASS | **200** |
| 4.4 Final state | PASS | `updated_at` advanced; status `Closed` |

### 5. Invalid transitions

| Step | Result | Evidence |
|------|--------|----------|
| 5.1 Open → Resolved | PASS | **409** `invalid_transition`, allowed: `In Progress`, `Cancelled` |
| 5.2 Closed → In Progress | PASS | **409** `invalid_transition`, allowed: `none` |

### 6. Comments

| Step | Result | Evidence |
|------|--------|----------|
| 6.1 List comments | PASS | Ticket 1 has seeded comment |
| 6.2 Add on Resolved | PASS | **201** on ticket 13 (while Resolved), author included |
| 6.3 Comment on Cancelled | PASS | Ticket 5 → **409** `comment_not_allowed` |

### 7. CSV export

| Step | Result | Evidence |
|------|--------|----------|
| 7.1 Export Dave's tickets | PASS | **200**, `text/csv`, `Content-Disposition: attachment; filename="tickets_user_4.csv"`, header + 8 data rows (all statuses) |
| 7.2 Invalid user | PASS | `created_by=9999` → **404** |

### 8. Persistence

| Step | Result | Evidence |
|------|--------|----------|
| 8.1–8.4 Restart survival | PASS | Server stopped/restarted; ticket 13 still `Closed` with updated title; `total: 13` (12 seeded + 1 created) |

### 9. Error shape

| Step | Result | Evidence |
|------|--------|----------|
| 9.1 Standard shape | PASS | All 422/404/409 responses use `{"error": {"code", "message", "details"}}`; no stack traces or HTML |

---

## UI Smoke Test (manual, via browser)

**Date:** 2026-07-19  
**Environment:** Vite dev server on `:5173` proxying to backend on `:8000`  
**UI:** http://localhost:5173  
**Result:** **14/14 checks passed**, 0 failures

| Check | Steps performed | Result |
|-------|-----------------|--------|
| View tickets from DB | Loaded list page | PASS — 13 tickets rendered (14 after create), priority/status badges, assignee + creator columns |
| Search | Typed lowercase `vpn` in search box | PASS — 1 match "VPN not connecting", case-insensitive |
| Filter | Selected status = Open | PASS — exactly the 3 Open tickets shown |
| Backend validation surfaced in UI | Submitted create form with 2-char title `ab` | PASS — POST /api/tickets returned 422 (confirmed in network tab, so backend validation, not HTML5) and the Pydantic message "String should have at least 3 characters" rendered as an inline field error |
| Create ticket via UI | Created "UI smoke test ticket" as acting-as user Alice Admin, priority High, assignee Bob Agent | PASS — ticket #14 created with `created_by` = acting-as user, redirected to detail page, status Open |
| Detail view | Opened #14 | PASS — badges, creator, timestamp, editable details |
| Update fields + reassign | Edited title to "UI smoke test ticket (edited)", changed assignee Bob Agent → Carol Manager, saved | PASS — persisted (verified via `GET /api/tickets/14`) |
| Status change via UI | Clicked "Move to In Progress" on #14 | PASS — badge updated to In Progress; action buttons changed from [In Progress, Cancelled] to [Resolved, Cancelled] |
| Valid-transitions-only UI | Observed Status Actions per status | PASS — UI only ever offers transitions allowed by the state machine |
| Add comment | Posted a comment on #14 | PASS — rendered with author = acting-as user and timestamp |
| Terminal state: Closed | Opened #4 | PASS — "read-only" banner, no status buttons, no Save button, comment form replaced by "Comments are disabled for tickets in Closed status." |
| Terminal state: Cancelled | Opened #5 | PASS — same read-only treatment |
| CSV export via UI | Clicked "Export my tickets (CSV)" as Alice Admin | PASS — `GET /api/tickets/export?created_by=1` returned 200 `text/csv` |
| Console errors | Reviewed browser console for the whole session | PASS — zero errors |

### Summary

All Core acceptance criteria are now verified end-to-end — API-level via the earlier Swagger/curl smoke test (including persistence across restart and 409s for invalid transitions) and UI-level via this browser pass.

**Two-layer state machine enforcement:** the frontend prevents invalid transitions by only rendering valid action buttons (and none in terminal states), while the backend independently rejects invalid transitions with **409**.

---

## README dry run (clean copy)

**Date:** 2026-07-19  
**Method:** Fresh rsync copy to `/tmp/ai-practical-assessment-dryrun` (excluded `venv/`, `node_modules/`, `*.db`, `.env`, `.git`); followed `README.md` steps  
**Result:** **PASS**

| Step | Result | Evidence |
|------|--------|----------|
| `python3 -m venv venv` + `pip install -r requirements.txt` | PASS | Dependencies installed |
| `cp .env.example .env` | PASS | Default `DATABASE_URL` |
| `alembic upgrade head` | PASS | Migration `001` applied |
| `python -m src.backend.seed` | PASS | "Seed data inserted successfully." |
| `pytest -q` | PASS | **49 passed**, 0 failed |
| `uvicorn ... --port 8001` + health check | PASS | `{"status":"ok"}` (used 8001 — port 8000 occupied by dev session) |
| `cd src/frontend && npm install && npm run build` | PASS | Vite production build succeeded |

**Note:** `npm run dev` not started in dry-run copy (port 5173 already in use by active dev session); production build confirms frontend compiles and bundles.

---

## UI error-state verification (manual browser)

**Date:** 2026-07-19 (validation) / 2026-07-20 (auth)  
**Environment:** Dev servers (`:5173` → `:8000`)  
**Tool:** Manual browser UI smoke test  
**Result:** Error states surfaced correctly in every case observed

| Check | Steps performed | Result |
|-------|-----------------|--------|
| Validation error (422) | Submitted the create form with a 2-char title | PASS — real `POST /api/tickets` → 422 (confirmed in the network tab, not HTML5), Pydantic message rendered inline under the field |
| Auth error banner | Submitted login with a wrong password | PASS — "Invalid email or password" shown in a dismissible banner; no navigation |
| Invalid transition (409) | Verified at the API level; the UI prevents it by only rendering valid status actions and locking terminal-state tickets read-only | PASS — no path to trigger an invalid transition from the UI; 409 error shape confirmed via the API smoke test above |

---

## Known gaps (not blocking)

From `test-strategy.md` — acceptable for Day 1; address on Day 2 if time permits:

- **CSV special-char quoting** — scheduled Day 2 test (`test_csv_export_escapes_special_characters`); see `test-strategy.md`
- Frontend e2e — manual UI smoke completed (see UI Smoke Test section above)

---

## Post-smoke observations (not failures — Day 2/3 polish)

1. **Timestamp precision inconsistent** — seeded rows return `2026-07-19T13:33:03`; updated rows include microseconds (`...16:12:45.372199`). Cosmetic; consider normalizing `updated_at` serialization or DB column precision for tidier UI display.

2. **CSV quoting** — covered by `test_csv_export_quotes_commas_quotes_and_newlines` in `tests/test_ticket_api.py` (added post–Day 1).

---

## Post-JWT verification (2026-07-20)

JWT authentication stretch merged to `main`. This section supersedes pre-JWT mutation/export checks above.

### Automated tests (current)

**Date:** 2026-07-20  
**Command:** `venv/bin/python -m pytest -q`  
**Result:** **91 passed**, 0 failed

| Suite | File | Tests |
|-------|------|-------|
| State machine unit | `tests/test_state_machine_unit.py` | 16 |
| State machine integration | `tests/test_state_machine_integration.py` | 13 |
| Ticket API | `tests/test_ticket_api.py` | 30 |
| Auth API | `tests/test_auth_api.py` | 19 |
| Auth permissions | `tests/test_auth_permissions.py` | 13 |

### Post-JWT API smoke (TestClient)

**Date:** 2026-07-20  
**Method:** One-shot script using `fastapi.testclient.TestClient` against the real app (in-memory SQLite test DB)  
**Result:** **17/17 checks passed**, 0 failures

| Step | Result | Evidence |
|------|--------|----------|
| 0.1 Login Alice | PASS | `POST /api/auth/login` → 200, `access_token` present |
| 0.2 Health (public) | PASS | `{"status":"ok"}` without auth |
| 0.3 Users (public) | PASS | 4 seeded users without auth |
| 1.1 List tickets (public) | PASS | `GET /api/tickets` → 200, `total >= 12` |
| 1.2 Filter status | PASS | `status=Open` filter works |
| 2.1 Create without auth rejected | PASS | `POST /api/tickets` → **401** |
| 2.2 Create with JWT | PASS | **201**, status `Open` |
| 2.3 `created_by` from token | PASS | Alice's ticket has `created_by: 1` |
| 2.4 `created_by` in body rejected | PASS | Extra field → **422** |
| 4.1–4.3 Full lifecycle | PASS | Open → In Progress → Resolved → Closed |
| 5.1 Closed → In Progress rejected | PASS | **409** `invalid_transition` |
| 7.1 Export without auth | PASS | **401** |
| 7.2 Export with JWT | PASS | **200**, `text/csv` |
| 7.3 Export scoped to token user | PASS | Bob's export excludes Alice's smoke ticket |
| 8.1 Requester cannot change status | PASS | Dave → `POST …/status` → **403** |

Auth-specific behavior is also covered by `tests/test_auth_api.py` and `tests/test_auth_permissions.py` (login failures, `/me`, role scoping, comment/create `created_by` rejection).

### Post-JWT UI smoke (manual browser)

**Date:** 2026-07-20  
**Environment:** Vite dev server on `:5173` proxying to backend on `:8000`  
**Tool:** Manual browser UI smoke test  
**Login:** `alice@example.com` / `Password123` (all seeded users share this password)  
**Result:** **5/5 checks passed**, 0 failures

| Check | Result | Evidence |
|-------|--------|----------|
| Login redirect | PASS | `/` → `/login` when logged out; after Alice login → ticket list (`Support Tickets` heading) |
| Create ticket | PASS | `POST /api/tickets` body has no `created_by` field; header shows Alice Admin |
| Status actions by role | PASS | Dave on ticket #1 (own Open) — no `.status-actions`; Bob on #1 — "Move to" buttons visible |
| CSV export | PASS | `GET /api/tickets/export` with `Authorization: Bearer …`, no `created_by` query param |
| Logout / session | PASS | After logout, `/tickets/new` redirects to `/login` |

Pre-JWT UI smoke (14/14, 2026-07-19) remains valid for search, filters, validation banners, and terminal-state read-only behavior.

### README dry run (post-JWT)

**Status:** Not re-run to `/tmp` on 2026-07-20. Pre-JWT dry run (2026-07-19) passed through `npm run build`. Re-run with login step before production submission if required.
