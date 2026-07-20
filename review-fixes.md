# Review Fixes Log

Backend findings from `code-review-notes.md`, applied one at a time with test evidence.

---

## Fix 1 — Non-standard 500 body (Must-fix)

| | |
|---|---|
| **Finding** | Unhandled exceptions returned a non-contract response body instead of `{"error": {"code", "message", "details"}}`. |
| **Change** | Added global `@app.exception_handler(Exception)` in `src/backend/app/error_handlers.py` returning HTTP 500 with `code: "internal_error"`. Added regression test `test_internal_error_shape`. |
| **Test evidence** | `venv/bin/python -m pytest -q` → **50 passed** (includes `test_internal_error_shape`) |

---

## Fix 2 — CSV formula injection (Must-fix)

| | |
|---|---|
| **Finding** | Ticket title/description starting with `=`, `+`, `-`, or `@` could execute as spreadsheet formulas when the CSV is opened in Excel. |
| **Change** | Added `_sanitize_csv_cell()` in `ticket_service.py` to prefix risky cells with `'`. Added `test_csv_export_neutralizes_formula_injection`. |
| **Test evidence** | `venv/bin/python -m pytest -q` → **51 passed** |

---

## Fix 3 — Silent 10k export cap (Must-fix)

| | |
|---|---|
| **Finding** | CSV export used `limit=10000`, silently truncating users with more tickets. |
| **Change** | `export_tickets_csv()` now pages through results in batches of 500 until all rows are exported. |
| **Test evidence** | `venv/bin/python -m pytest -q` → **51 passed** (existing export tests) |

---

## Fix 4 — Search `q` LIKE wildcards (Should-fix)

| | |
|---|---|
| **Finding** | `%` and `_` in search query were treated as SQL wildcards (`GET ?q=100%` matched unintended rows). |
| **Change** | Added `_escape_like()` and `escape="\\"` on `ilike` filters. Added `test_search_treats_percent_as_literal`. |
| **Test evidence** | `venv/bin/python -m pytest -q` → **52 passed** |
