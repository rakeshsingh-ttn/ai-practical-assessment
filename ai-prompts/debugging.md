# Debugging

---

# Chat 8 — Fix loops and observations
_Exported on 7/19/2026 at 21:49:00 GMT+5:30 from Cursor (3.12.17)_

---

## Fix 1 — Port 8000 already in use

**When:** Chat 8a, starting uvicorn after prior session

**Symptom**
```
ERROR: [Errno 48] Address already in use
```

**Diagnosis**
```bash
lsof -i :8000 -sTCP:LISTEN
# Python  43469  ...  TCP localhost:irdmi (LISTEN)
```

Leftover uvicorn/Python process from earlier run (including background test from AI session).

**Fix**
```bash
kill 43469
# or: kill -9 43469 if needed
uvicorn src.backend.app.main:app --reload --port 8000
```

**Alternative:** use `--port 8001` and update frontend proxy if needed.

**Logged in:** `debugging-notes.md`

**Outcome:** User confirmed health endpoint `{"status":"ok"}` after restart.

---

## Fix 2 — PATCH assigned_to: null did not clear assignee

**When:** Chat 8d, reviewing endpoint wiring against acceptance criteria

**Symptom:** `PATCH {"assigned_to": null}` left stale assignee — only non-null values were applied.

**Root cause:** `if data.assigned_to is not None` treated explicit `null` same as omitted field.

**Fix:** `src/backend/app/services/ticket_service.py`
```python
if "assigned_to" in data.model_fields_set:
    if data.assigned_to is not None:
        get_user_or_404(db, data.assigned_to)
    ticket.assigned_to = data.assigned_to
```

**Test added:** `test_clear_assignee` in `tests/test_ticket_api.py`

**Commit:** `036014f` — feat: ticket, comment, user and csv endpoints

---

## Observation 1 — Timestamp precision inconsistent (not a failure)

**When:** Swagger smoke test, comparing seeded vs updated ticket timestamps

**Detail:**
- Seeded: `2026-07-19T13:33:03`
- Updated: `2026-07-19T16:12:45.372199` (microseconds)

**Impact:** Cosmetic UI inconsistency only.

**Day 2/3 polish:** Normalize datetime serialization (e.g. strip microseconds in Pydantic JSON encoder or align SQLite column precision).

**Logged in:** `test-results.md` → Post-smoke observations

---

## Observation 2 — CSV quoting untested (not a failure)

**When:** Swagger smoke test, CSV export for Dave (user 4)

**Detail:** All seeded descriptions are plain text — no commas, quotes, or newlines. `csv.writer` used but never proven under nasty input.

**Day 2 action:** Integration test `test_csv_export_escapes_special_characters`
- Create ticket with `description = 'Says "hello", world\nSecond line'`
- Export CSV, parse with `csv.reader`, assert round-trip

**Logged in:** `test-strategy.md` → Day 2 Planned integration tests

---

## Smoke test — no failures

**Date:** 2026-07-19  
**Result:** 27/27 Swagger checks pass, 35/35 pytest pass

No bugs filed from smoke test. Full evidence in `test-results.md`.
