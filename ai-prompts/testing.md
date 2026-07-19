# Testing

---

# Chat 9 — UI smoke test results
_Exported on 7/19/2026 at 22:10:00 GMT+5:30 from Cursor (3.12.17)_

---

## 9a — Record manual UI smoke test

**User**

I completed a manual UI smoke test of the frontend in the browser (dev server on `:5173` proxying to the backend on `:8000`). Append a new section `## UI Smoke Test (manual, via browser)` to `test-results.md`, matching the existing document's style, with today's date. Record these results exactly:

| Check | Steps performed | Result |
|---|---|---|
| View tickets from DB | Loaded list page | PASS — 13 tickets rendered (14 after create), priority/status badges, assignee + creator columns |
| Search | Typed lowercase "vpn" in search box | PASS — 1 match "VPN not connecting", case-insensitive |
| Filter | Selected status = Open | PASS — exactly the 3 Open tickets shown |
| Backend validation surfaced in UI | Submitted create form with 2-char title "ab" | PASS — POST /api/tickets returned 422 (confirmed in network tab, so backend validation, not HTML5) and the Pydantic message "String should have at least 3 characters" rendered as an inline field error |
| Create ticket via UI | Created "UI smoke test ticket" as acting-as user Alice Admin, priority High, assignee Bob Agent | PASS — ticket #14 created with created_by = acting-as user, redirected to detail page, status Open |
| Detail view | Opened #14 | PASS — badges, creator, timestamp, editable details |
| Update fields + reassign | Edited title to "UI smoke test ticket (edited)", changed assignee Bob Agent → Carol Manager, saved | PASS — persisted (verified via GET /api/tickets/14) |
| Status change via UI | Clicked "Move to In Progress" on #14 | PASS — badge updated to In Progress; action buttons changed from [In Progress, Cancelled] to [Resolved, Cancelled] |
| Valid-transitions-only UI | Observed Status Actions per status | PASS — UI only ever offers transitions allowed by the state machine |
| Add comment | Posted a comment on #14 | PASS — rendered with author = acting-as user and timestamp |
| Terminal state: Closed | Opened #4 | PASS — "read-only" banner, no status buttons, no Save button, comment form replaced by "Comments are disabled for tickets in Closed status." |
| Terminal state: Cancelled | Opened #5 | PASS — same read-only treatment |
| CSV export via UI | Clicked "Export my tickets (CSV)" as Alice Admin | PASS — GET /api/tickets/export?created_by=1 returned 200 text/csv |
| Console errors | Reviewed browser console for the whole session | PASS — zero errors |

Summary to include: all Core acceptance criteria are now verified end-to-end — API-level via the earlier Swagger/curl smoke test (including persistence across restart and 409s for invalid transitions) and UI-level via this browser pass. Note the two-layer state machine enforcement: the frontend prevents invalid transitions by only rendering valid action buttons (and none in terminal states), while the backend independently rejects invalid transitions with 409.

Then update `acceptance-criteria.md`: tick every checkbox this UI pass proves (create via UI, view all tickets, detail view, update fields and reassign, add comments, status only through valid transitions, backend validation prevents invalid records, CSV export). Leave anything not yet proven unticked. Don't change any other files.

**Cursor**

Updated `test-results.md` and `acceptance-criteria.md` only.

**`test-results.md`**
- Added **## UI Smoke Test (manual, via browser)** (2026-07-19)
- Environment: Vite `:5173` → backend `:8000`
- **14/14 checks passed**
- Full results table and summary (API + UI end-to-end; two-layer state machine)
- Known gaps note updated: frontend e2e manual UI smoke completed

**`acceptance-criteria.md` — ticked from UI pass**

| Section | Items ticked |
|---------|--------------|
| Core | Create via UI, View all tickets, Detail view, Update/reassign, Add comments, Status via valid transitions, Backend validation, CSV export, Search/filter, Acting-as |
| Validation | Title required |
| Error Handling | UI inline validation errors, Disabled UI on terminal tickets |

Left unticked: Data survives restart (not UI-proven), state-machine integration tests, no secrets, no delete, remaining Validation/Error Handling/Testing/Documentation items.

---

## 9b — Tick data survives restart

**User**

data servived

**Cursor**

Ticked **Data survives restart** in `acceptance-criteria.md`. Already proven in Swagger smoke test section 8 (server stop/restart; ticket #13 still `Closed`; `total: 13`).

---

## 9c — Open points review

**User**

what is still open now or any opne point ?

**Cursor**

Status summary after Day 1 (backend + both smoke passes):

**Core still unchecked (3):**
- State-machine integration tests pass — likely done (35 pytest pass); checkbox not ticked
- No secrets in repo — needs repo audit
- No delete — likely done (no DELETE endpoint/UI); not ticked

**Validation (13 unchecked)** — mostly Swagger-proven but not ticked; gaps: max lengths, whitespace-only comment

**Error Handling (6 unchecked)** — API proven in Swagger; UI gaps: 409 banners, friendly 409 on rejected transition

**Testing (19 unchecked)** — work largely done; checkbox audit needed (pytest 35/35, Swagger 27/27, UI 14/14)

**Documentation (6 unchecked)** — README dry run, artifact sign-off

**Known test gaps:** same-status no-op, filter integration tests, whitespace comment, CSV special-char quoting

**Polish:** timestamp precision, CSV quoting, Resolved read-only UI not spot-checked

**Day 3 stubs empty:** `candidate-info.md`, `reflection.md`, `code-review-notes.md`, `review-fixes.md`, `pr-description.md`, `final-ai-usage-summary.md`

**Next steps suggested:** acceptance-criteria audit pass, repo audit, missing integration tests, Day 3 artifacts, optional UI spot-checks (Resolved read-only, 409 banners).

---

## Outcome

**Result:** 14/14 UI smoke checks pass; Core acceptance criteria verified end-to-end (API Swagger + browser UI).

**Evidence:** `test-results.md` → UI Smoke Test section; `acceptance-criteria.md` → 12 Core/Validation/Error Handling boxes ticked.

**Commit:** `docs: record UI smoke test results and export that chat into ai-prompts/testing.md`
