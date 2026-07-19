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
