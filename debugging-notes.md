# Debugging Notes

## 2026-07-19 — Port 8000 already in use

**Symptom:** `uvicorn ... --port 8000` → `ERROR: [Errno 48] Address already in use`

**Cause:** Leftover Python/uvicorn process from a prior run (PID 43469).

**Fix:** `kill <pid>` then restart uvicorn.

**Lesson:** Stop the dev server with Ctrl+C before starting a new one, or use `lsof -i :8000` to find stale processes.

---

## 2026-07-19 — Swagger smoke test (27/27 pass)

**Context:** Manual smoke test via `/docs` after wiring all API endpoints (Chat 8e).

**Issues found:** None.

**Notes:**
- Created ticket **13** for lifecycle testing (Open → In Progress → Resolved → Closed).
- All validation, transition, comment, CSV, persistence, and error-shape checks passed.
- Full results logged in [test-results.md](test-results.md).
- Two polish observations (not failures): timestamp precision inconsistency; CSV quoting untested — see test-results.md and Day 2 planned test in test-strategy.md.

---

## 2026-07-20 — AI-generated code mistakes caught in the code-review pass

These are the concrete bugs the AI's own generated backend shipped with. They
did not fail the happy path or the demo — each was found by reviewing/​testing
the boundary inputs the feature was never exercised with. Each was fixed in its
own commit (see also [review-fixes.md](review-fixes.md)).

### CSV formula injection — commit `70d7715`

**Problem:** The generated CSV export wrote ticket fields into cells verbatim. A
ticket whose title starts with `=`, `+`, `-`, or `@` executes as a formula when
the export is opened in Excel/Sheets — user-controlled input becoming executable
in the one feature designed to leave the system.

**How I found it:** A security-focused prompt in the code-review pass, asking
specifically what could go wrong in the export. Nothing in normal testing catches
it because the CSV is "valid".

**Fix:** Added `_sanitize_csv_cell()` in `ticket_service.py` that prefixes risky
cells, plus regression test `test_csv_export_neutralizes_formula_injection`.

### Search wildcard injection — commit `677475a`

**Problem:** The `q` search term was passed into a SQL `LIKE` unescaped, so `%`
and `_` acted as wildcards. Searching `100%` silently matched **every** ticket —
wrong results returned with a 200 status, the worst kind of bug.

**How I found it:** Throwing edge-case inputs (literal `%`) at the filter during
review.

**Fix:** Escape `%` and `_` before building the `LIKE` pattern; added a test with
wildcard characters in the query.

### Silent 10k export cap — commit `2ffcccd`

**Problem:** Export used `limit=10000`, silently truncating any larger result set
— data loss with no error surfaced.

**Fix:** `export_tickets_csv()` now pages through results in batches until
complete.

**Lesson (all three):** AI-generated code fails quietly at the edges. It passes
the happy path and the demo, so my review effort goes to the inputs the feature
was never demoed with.

---

## 2026-07-20 — CSV export leaked any user's data (found in manual auth testing)

**Problem:** The first cut of the JWT auth stretch left `GET /api/tickets/export`
unauthenticated and trusting a client-supplied `created_by` query parameter. So
any caller — with no token at all — could download any user's tickets by changing
the number, and the Core "export **self-generated** tickets" semantics was broken.

**How I found it:** Manual API security testing of the auth work before committing
it. `GET /api/tickets/export` with no `Authorization` header returned `200` with
full data; logged in as Dave, `?created_by=1` returned Alice's tickets.

**Fix:** Export now requires a valid JWT and derives the user from the token
(`current_user.id`); the `created_by` parameter is ignored. Verified after the
fix: `401` with no token, and the parameter is inert with one (Dave only ever
gets his own 8 rows). Because this was caught before the auth branch was
committed, the correct behaviour is part of the auth feature commit `1d3a6ab`
(merged in `13fe93b`) rather than a standalone fix.

**Lesson:** Generated auth guarded the *mutating* routes but left a *read/export*
route open — the gaps are where the generator's attention wasn't. Manual testing
of the actual endpoints, not just green unit tests, is what caught it.
