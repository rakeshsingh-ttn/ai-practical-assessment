# Review Fixes Log

Backend findings from `code-review-notes.md`, applied and committed one fix at a time with test evidence after each change.

**Final suite:** `venv/bin/python -m pytest -q` → **56 passed**

---

## Fix 1 — Non-standard 500 body (Must-fix)

| | |
|---|---|
| **Finding** | Unhandled exceptions returned a non-contract response body instead of `{"error": {"code", "message", "details"}}`. |
| **Change** | Added global `@app.exception_handler(Exception)` in `error_handlers.py` returning HTTP 500 with `code: "internal_error"`. Added `test_internal_error_shape`. |
| **Commit** | `fix: return standard 500 error shape for unhandled exceptions (from code review)` |
| **Test evidence** | 50 passed |

---

## Fix 2 — CSV formula injection (Must-fix)

| | |
|---|---|
| **Finding** | Ticket fields starting with `=`, `+`, `-`, or `@` could execute as spreadsheet formulas when CSV is opened in Excel. |
| **Change** | Added `_sanitize_csv_cell()` in `ticket_service.py`. Added `test_csv_export_neutralizes_formula_injection`. |
| **Commit** | `fix: prefix risky CSV cells to prevent spreadsheet formula injection (from code review)` |
| **Test evidence** | 51 passed |

---

## Fix 3 — Silent 10k export cap (Must-fix)

| | |
|---|---|
| **Finding** | CSV export used `limit=10000`, silently truncating large result sets. |
| **Change** | `export_tickets_csv()` pages through results in batches of 500 until complete. |
| **Commit** | `fix: page CSV export instead of silently truncating at 10k rows (from code review)` |
| **Test evidence** | 51 passed |

---

## Fix 4 — Search `q` LIKE wildcards (Should-fix)

| | |
|---|---|
| **Finding** | `%` and `_` in `q` were treated as SQL wildcards (`GET ?q=100%` matched unintended rows). |
| **Change** | Added `_escape_like()` and `escape="\\"` on `ilike`. Added `test_search_treats_percent_as_literal`. |
| **Commit** | `fix: escape LIKE wildcards in ticket search query (from code review)` |
| **Test evidence** | 52 passed |

---

## Fix 5 — TOCTOU on edit/comment/status (Should-fix)

| | |
|---|---|
| **Finding** | Concurrent PATCH and status change could race without row-level locking. |
| **Change** | Added `_get_ticket_for_update()` with `with_for_update()` for mutating operations. |
| **Commit** | `fix: lock ticket rows on update, status change, and comment create (from code review)` |
| **Test evidence** | 52 passed |

---

## Fix 6 — Whitespace-only title (Should-fix)

| | |
|---|---|
| **Finding** | `POST` with `title: "   "` passed `min_length` because spaces counted toward length. |
| **Change** | Strip title on create/update; reject if fewer than 3 non-whitespace characters. Added `test_whitespace_only_title_rejected`. |
| **Commit** | `fix: reject whitespace-only ticket titles after stripping (from code review)` |
| **Test evidence** | 53 passed |

---

## Fix 7 — IntegrityError handler (Should-fix)

| | |
|---|---|
| **Finding** | DB constraint violations could surface as unhandled 500s. |
| **Change** | Added `@app.exception_handler(IntegrityError)` returning `409 integrity_error`. |
| **Commit** | `fix: map database IntegrityError to standard 409 response (from code review)` |
| **Test evidence** | 53 passed |

---

## Fix 8 — Duplicated filter logic (Should-fix)

| | |
|---|---|
| **Finding** | List and count queries duplicated identical filter clauses (maintenance drift risk). |
| **Change** | Extracted `_ticket_filter_clauses()` shared by list and count paths. |
| **Commit** | `fix: extract shared ticket filter clauses for list and count queries (from code review)` |
| **Test evidence** | 53 passed |

---

## Fix 9 — Extra JSON fields ignored (Should-fix)

| | |
|---|---|
| **Finding** | Unknown fields (e.g. `status` on PATCH) were silently ignored instead of rejected. |
| **Change** | Set `extra="forbid"` on ticket/comment request schemas. Added tests; updated `test_status_cannot_be_changed_via_patch` to expect 422. |
| **Commit** | `fix: reject unknown JSON fields on ticket and comment request bodies (from code review)` |
| **Test evidence** | 56 passed |

---

## Fix 10 — DB CHECK constraints (Should-fix)

| | |
|---|---|
| **Finding** | Enum columns relied only on application validation; direct SQL could insert invalid values. |
| **Change** | Added migration `002_check_constraints.py` for `tickets.status`, `tickets.priority`, `users.role`. |
| **Commit** | `fix: add database CHECK constraints for status, priority, and role enums (from code review)` |
| **Test evidence** | 56 passed |

---

## Fix 11 — Session rollback (Should-fix)

| | |
|---|---|
| **Finding** | Failed request handlers did not explicitly roll back the SQLAlchemy session. |
| **Change** | `get_db()` now calls `db.rollback()` before re-raising on exception. |
| **Commit** | `fix: explicitly rollback database session on request handler errors (from code review)` |
| **Test evidence** | 56 passed |

---

## Fix 12 — Comment list over-fetch (Should-fix)

| | |
|---|---|
| **Finding** | Listing comments loaded the full ticket row only to verify existence. |
| **Change** | Replaced `get_ticket_or_404()` with `EXISTS` subquery in `list_comments()`. |
| **Commit** | `fix: use EXISTS check instead of loading full ticket for comment list (from code review)` |
| **Test evidence** | 56 passed |

---

## Fix 13 — Empty PATCH bumps `updated_at` (Nit)

| | |
|---|---|
| **Finding** | Empty PATCH body still committed and bumped `updated_at`. |
| **Change** | Return early when `model_fields_set` is empty. |
| **Commit** | `fix: no-op PATCH requests without bumping updated_at (from code review)` |
| **Test evidence** | 56 passed |

---

## Fix 14 — Post-commit re-fetch (Nit)

| | |
|---|---|
| **Finding** | `update_ticket` and `change_ticket_status` re-queried after commit despite already holding the row. |
| **Change** | Return `db.refresh(ticket)` result instead of `get_ticket_or_404()` after PATCH/status change. |
| **Commit** | `fix: return refreshed ticket after PATCH instead of re-querying (from code review)` |
| **Test evidence** | 56 passed |

---

## Fix 15 — `scalar_one_or_none` vs `db.get` (Nit)

| | |
|---|---|
| **Finding** | Ticket lookup by PK used a heavier `select` query than necessary. |
| **Change** | `get_ticket_or_404()` now uses `db.get()` with `joinedload` options. |
| **Commit** | `fix: load tickets by primary key with joined relationships (from code review)` |
| **Test evidence** | 56 passed |

---

## Fix 16 — Lazy import in `ticket_status` (Nit)

| | |
|---|---|
| **Finding** | `InvalidTransitionError` was imported inside `transition()` instead of at module level. |
| **Change** | Moved import to top of `ticket_status.py`. |
| **Commit** | `fix: import InvalidTransitionError at module level in ticket_status (from code review)` |
| **Test evidence** | 56 passed |

---

## Fix 17 — Unknown `AppError` mapped to 400 (Nit)

| | |
|---|---|
| **Finding** | Unrecognized `AppError` codes returned HTTP 400 instead of 500. |
| **Change** | Unknown codes now map to `500 internal_error` in standard shape. |
| **Commit** | `fix: map unknown AppError codes to 500 instead of 400 (from code review)` |
| **Test evidence** | 56 passed |

---

## Fix 18 — CSV charset (Nit)

| | |
|---|---|
| **Finding** | CSV export `Content-Type` omitted charset. |
| **Change** | Set `media_type="text/csv; charset=utf-8"` on export response. |
| **Commit** | `fix: include charset in CSV export Content-Type header (from code review)` |
| **Test evidence** | 56 passed |

---

## Fix 19 — Seed `create_all` bypass (Nit)

| | |
|---|---|
| **Finding** | `python -m src.backend.seed` called `Base.metadata.create_all()`, bypassing Alembic migrations. |
| **Change** | Removed `create_all` from `__main__`; seed now assumes migrations were applied first. |
| **Commit** | `fix: require Alembic migrations before seeding instead of create_all (from code review)` |
| **Test evidence** | 56 passed |
