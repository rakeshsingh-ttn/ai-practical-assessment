# Code Review

---

# Chat 10 — Backend code review and fixes
_Exported on 7/20/2026 at 10:05:00 GMT+5:30 from Cursor (3.12.17)_

---

## 10a — Strict AI backend review

**User**

Act as a strict senior Python reviewer. Review the backend under `src/backend/` against `api-contract.md`, `design-notes.md` and the state-machine rule. Do NOT change any code — produce review findings only.

For each finding give: file:line, severity (must-fix / should-fix / nit), the issue, and the suggested change. Cover specifically:
- correctness: transitions, edit-allowed rules, comment rules, CSV filtering
- consistency with the documented error shape and status codes (422/404/409)
- validation gaps
- SQLAlchemy usage: session handling, N+1 queries on list endpoints
- security basics: SQL injection surface, CSV injection, secrets in code
- code quality: dead code, duplication, naming, router/service layering leaks
Order findings by severity. Be critical — I want real findings, not praise.

**Cursor**

Produced a structured review with **21 findings**:
- **3 must-fix:** non-standard 500 error shape; CSV formula injection; silent 10k-row export cap
- **9 should-fix:** session rollback; `LIKE` wildcard search; duplicated filter logic; TOCTOU on edit/comment; `IntegrityError` handler; whitespace title; comment list over-fetch; `extra` fields silently ignored; missing DB CHECK constraints
- **9 nits:** empty PATCH bumps `updated_at`; redundant re-fetch; lazy import; unknown `AppError` → 400; CSV charset; seed `create_all`; etc.

Noted positives briefly (state machine isolation, `joinedload` on list, no SQL injection via ORM) but focused on defects per request.

---

## 10b — Concrete failure scenario triage

**User**

For each must-fix and should-fix, tell me the concrete failure scenario — what input or sequence makes it break in practice? If you can't name one, downgrade it. I'll then decide which to accept and which to reject.

**Cursor**

Triaged every must-fix and should-fix with repro steps or downgrade rationale.

**Kept as high-value:**
| Finding | Repro |
|---------|-------|
| 500 error shape | Any unhandled exception / ops failure → wrong JSON |
| CSV injection | `POST` title `=cmd\|'/c calc'!A0` → export → open in Excel |
| Search wildcards | `GET ?q=100%` matches unintended tickets |
| TOCTOU | Parallel PATCH + status change on same ticket |
| Whitespace title | `POST` title `"   "` → 201 with meaningless title |

**Downgraded (no practical repro in demo):**
- 10k CSV cap (needs >10k tickets per user)
- Session rollback (SQLAlchemy `close()` already rolls back)
- Duplicate filters (no current drift)
- IntegrityError handler (not API-reproducible today)
- Comment over-fetch (performance only)
- Extra fields ignored (matches contract)
- DB CHECK constraints (requires raw SQL)

**Summary:** 3 must-fix + 5 should-fix with clear repros; rest downgraded to nit/latent.

---

## 10c — Accept all findings

**User**

accept all

**Cursor**

Implemented all 21 findings (including downgraded nits):

**`error_handlers.py`** — global `500` `internal_error` shape; `IntegrityError` → `409`; unknown `AppError` → `500`

**`database.py`** — explicit `rollback()` on exception in `get_db()`

**`ticket_service.py`** — CSV cell sanitization; batched export (500 rows); `_escape_like` for search; `_ticket_filter_clauses` helper; `_get_ticket_for_update()` with `with_for_update()`; `exists()` for comment list; empty PATCH no-op

**`schemas/__init__.py`** — title strip/validate; `extra="forbid"` on request models

**`ticket_status.py`** — top-level `InvalidTransitionError` import

**`routers/tickets.py`** — `text/csv; charset=utf-8`

**`seed.py`** — removed `create_all` from `__main__`

**`002_check_constraints.py`** — CHECK on ticket status/priority and user role

**Tests added:** whitespace title, extra fields, literal `%` search, CSV formula prefix, 500 error shape, PATCH rejects `status` field; integration test split for status-on-PATCH behavior

**Result:** **55 tests passed**

**Contract note:** `extra="forbid"` changes PATCH `status` from “ignored” to **422**.

---

## 10d — Write code-review-notes.md

**User**

Write `code-review-notes.md` using my decisions above:
- ## AI-Assisted Review Summary
- ## My Review Observations
- ## Changes Made After Review
- ## Suggestions Rejected (and why)

**Cursor**

Wrote `code-review-notes.md` with:
- AI summary (scope, 21 finding counts, triage table, accept-all decision)
- Seven manual observations (layering, N+1, `extra=forbid` vs contract, timestamps, frontend mirror, 55 tests, migration 002)
- Five planned implementation commits mapping findings to files
- No rejected AI findings; table of alternative approaches considered (silent PATCH status, document cap, defer CHECKs, skip global 500 handler)

---

## Outcome

**Review artifact:** `code-review-notes.md`  
**Implementation:** Backend hardening uncommitted in working tree at export time (planned as 5 fix/test commits)  
**Export commit:** `docs: backend code review notes` + `ai-prompts/code-review.md`
