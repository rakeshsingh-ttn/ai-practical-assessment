# Code Review Notes

**Date:** 2026-07-20  
**Scope:** `src/backend/` reviewed against `api-contract.md`, `design-notes.md`, and the ticket status state machine rule (`.cursor/rules/20-state-machine.mdc`).  
**Method:** AI-assisted strict review in Cursor, then manual triage of each finding against a concrete failure scenario, then implementation of all accepted items.

---

## AI-Assisted Review Summary

The AI review covered the full backend under `src/backend/`:

| Area | What was checked |
|------|------------------|
| **Correctness** | State machine transitions, edit-allowed statuses, comment-allowed statuses, CSV `created_by` filtering |
| **API contract** | Error shape, HTTP status codes (422 / 404 / 409), PATCH vs status endpoint separation |
| **Validation** | Pydantic boundaries, fields that should be rejected, missing constraints |
| **SQLAlchemy** | Session lifecycle, N+1 on list/export endpoints |
| **Security** | SQL injection surface, CSV/Excel formula injection, secrets in code |
| **Code quality** | Duplication, layering leaks, dead code, naming |

### Finding counts (initial pass)

| Severity | Count | Examples |
|----------|-------|----------|
| **Must-fix** | 3 | Non-standard 500 body; CSV formula injection; silent 10k export cap |
| **Should-fix** | 9 | `LIKE` wildcard `q`; TOCTOU on edit/comment; whitespace title; `IntegrityError` handler; duplicated filters; `extra` fields ignored; DB CHECK constraints; session rollback; comment list over-fetch |
| **Nit** | 9 | Empty PATCH bumps `updated_at`; post-commit re-fetch; `scalar_one_or_none` vs `db.get`; lazy import; unknown `AppError` → 400; CSV charset; seed `create_all`; etc. |

**Total: 21 findings** (ordered by severity in the AI output).

### Triage pass (concrete failure scenarios)

Before implementing, I asked for a **concrete input or sequence** that breaks each finding in practice. That pass reclassified several items:

| Original | After triage | Reason |
|----------|--------------|--------|
| Must: 10k CSV cap | **Nit / scale-only** | Not reachable with seed + normal UI (&lt;10k tickets per user) |
| Should: session rollback | **Nit** | SQLAlchemy `Session.close()` already rolls back; no repro across requests |
| Should: duplicate filters | **Nit** | No current bug — maintenance risk only |
| Should: `IntegrityError` handler | **Nit** | Not API-reproducible without races or raw SQL |
| Should: comment over-fetch | **Nit** | Performance only |
| Should: `extra` fields ignored | **Nit** | Matches contract “ignored if sent” on PATCH |
| Should: DB CHECK constraints | **Nit** | Requires direct SQL bypass, not normal API |

**Kept as high-value after triage:** standard 500 shape (bugs/ops), CSV injection (one POST + export + Excel), search `%` wildcards (`GET ?q=100%`), TOCTOU (parallel PATCH + status), whitespace title (`POST title:"   "`).

**Decision:** Despite downgrades, I chose to **accept and implement all 21 findings** — cheap wins and defense-in-depth outweigh deferring “nit” items for a submission-quality codebase.

---

## My Review Observations

Things I noticed myself, beyond the AI’s numbered list:

1. **Layering holds.** Routers in `routers/tickets.py` stay thin; business rules live in `ticket_service.py` and `ticket_status.py`. The state machine is not bypassed on runtime status changes (seed bypass is documented and intentional).

2. **List endpoint is in good shape for N+1.** `joinedload` on creator/assignee was already correct; the AI’s main gap was the comment-list existence check loading a full ticket — easy to fix.

3. **`extra="forbid"` changes contract semantics.** The API contract says `status` on PATCH is “ignored if sent”; strict schemas now return **422**. I accepted this deliberately — silent ignore hid client bugs in manual testing. `api-contract.md` should be updated to match (planned follow-up).

4. **Timestamp precision** (seeded vs updated rows) remains cosmetic; not in the review list and not fixed here.

5. **Frontend mirrors backend transitions** (`constants.js` / `ALLOWED_TRANSITIONS`) — I spot-checked that invalid buttons are hidden; backend 409 remains the enforcement backstop.

6. **Test suite growth is appropriate.** Fixes added 6 tests (whitespace title, extra fields, literal `%` search, CSV formula prefix, 500 error shape, PATCH rejects `status`); full run is **55 passed** after changes.

7. **Migration required for CHECK constraints.** New `002_check_constraints.py` must be applied on existing DBs (`alembic upgrade head`); in-memory pytest still uses `create_all` without CHECKs — acceptable for unit tests.

---

## Changes Made After Review

All accepted findings are implemented in the working tree (see planned commits below).

### Commit 1 — `fix: standard error responses and session safety`
**Files:** `error_handlers.py`, `database.py`

| Finding | Change |
|---------|--------|
| Non-standard 500 body | Global `Exception` handler → `500` with `{"error": {"code": "internal_error", ...}}` |
| `IntegrityError` | Handler → `409` `integrity_error` in standard shape |
| Unknown `AppError` code | Maps to `500` instead of `400` |
| Session rollback | `get_db()` explicit `rollback()` on exception |

### Commit 2 — `fix: ticket service hardening (CSV, search, concurrency, export)`
**Files:** `ticket_service.py`, `routers/tickets.py`

| Finding | Change |
|---------|--------|
| CSV formula injection | `_sanitize_csv_cell()` prefixes risky leading characters with `'` |
| 10k export cap | Batch export in pages of 500 until all rows fetched |
| Search `q` wildcards | `_escape_like()` + `escape="\\"` on `ilike` |
| Duplicated filters | `_ticket_filter_clauses()` shared by list and count |
| TOCTOU edit/comment | `_get_ticket_for_update()` with `with_for_update()` |
| Comment list over-fetch | `exists()` check instead of full ticket load |
| Empty PATCH | No-op when `model_fields_set` empty; no `updated_at` bump |
| Post-commit re-fetch | Reduced redundant refresh where possible; `db.get()` for reads |
| CSV charset | `text/csv; charset=utf-8` |

### Commit 3 — `fix: stricter request validation on ticket and comment schemas`
**Files:** `schemas/__init__.py`, `ticket_status.py`, `seed.py`

| Finding | Change |
|---------|--------|
| Whitespace-only title | Strip + min 3 non-whitespace characters |
| Extra JSON fields | `extra="forbid"` on `TicketCreate`, `TicketUpdate`, `TicketStatusUpdate`, `CommentCreate` |
| Lazy import | `InvalidTransitionError` imported at module top in `ticket_status.py` |
| Seed `create_all` | Removed from `__main__`; Alembic required first |

### Commit 4 — `feat: add DB CHECK constraints for enum columns`
**Files:** `database/migrations/versions/002_check_constraints.py`

| Finding | Change |
|---------|--------|
| DB enum enforcement | CHECK on `tickets.status`, `tickets.priority`, `users.role` |

### Commit 5 — `test: regression coverage for code review fixes`
**Files:** `tests/test_ticket_api.py`, `tests/test_state_machine_integration.py`

- Whitespace title → 422  
- Extra field (`status` on create) → 422  
- Literal `%` in search  
- CSV export neutralizes `=1+1`  
- 500 returns standard error shape  
- PATCH with `status` field → 422; PATCH title-only leaves status unchanged  

---

## Suggestions Rejected (and why)

**None in the final pass.**

After the concrete-failure triage, I did **not** reject any AI finding for implementation. Several were downgraded in *severity* (see table above) because they lack a practical repro in the current demo — but I still implemented them for consistency and future-proofing.

### Alternatives considered but not taken

| Alternative | Why rejected |
|-------------|--------------|
| **Leave PATCH `status` as silently ignored** (per original contract wording) | Chose `extra="forbid"` → 422 so client mistakes surface immediately during UI and API testing. |
| **Document 10k export cap instead of batching** | Silent truncation is worse than a few extra lines of pagination; batching is low cost. |
| **Defer CHECK constraints to “Postgres only”** | SQLite is the assessed default; CHECKs in migration 002 align `design-notes.md` with reality. |
| **Skip global 500 handler** (only fix known paths) | Contract requires one error shape for all API failures; unhandled exceptions are inevitable in production. |

No AI suggestions were left unimplemented after the “accept all” decision.
