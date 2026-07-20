# Review Fixes Log

Backend findings from `code-review-notes.md`, applied one at a time with test evidence.

---

## Fix 1 — Non-standard 500 body (Must-fix)

| | |
|---|---|
| **Finding** | Unhandled exceptions returned a non-contract response body instead of `{"error": {"code", "message", "details"}}`. |
| **Change** | Added global `@app.exception_handler(Exception)` in `src/backend/app/error_handlers.py` returning HTTP 500 with `code: "internal_error"`. Added regression test `test_internal_error_shape`. |
| **Test evidence** | `venv/bin/python -m pytest -q` → **50 passed** (includes `test_internal_error_shape`) |
