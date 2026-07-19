# Test Strategy

## Test Scope

| Tier | Tool | What it covers | Location |
|------|------|----------------|----------|
| **Unit** | pytest | State machine `can_transition` matrix; terminal states; ALLOWED_TRANSITIONS completeness | `tests/test_state_machine_unit.py` |
| **Integration / API** | pytest + FastAPI `TestClient` | Full HTTP stack against real app with in-memory SQLite | `tests/test_state_machine_integration.py`, `tests/test_ticket_api.py` |
| **Manual smoke** | Swagger UI (`/docs`) + browser | End-to-end API flows not covered by automation; all UI flows | Acceptance checklist in `acceptance-criteria.md` |
| **Frontend e2e** | — | **Not covered** — skipped for time (see below) | — |

**Test database:** in-memory SQLite (`sqlite://` with `StaticPool`) via `conftest.py` fixtures. Each test gets a fresh schema; no mocks for HTTP or DB layer.

**Run:** `pytest -v` from project root.

---

## Unit Tests

### State machine (`test_state_machine_unit.py`)

| Test | Asserts |
|------|---------|
| `test_can_transition` (parametrized) | Every valid pair returns `True`; representative invalid pairs return `False` |
| `test_allowed_transitions_cover_all_statuses` | `ALLOWED_TRANSITIONS` keys == all `TicketStatus` values |
| `test_terminal_states_have_no_outgoing_transitions` | `Closed` and `Cancelled` map to empty sets |

**Valid transitions tested:**

- Open → In Progress, Cancelled
- In Progress → Resolved, Cancelled
- Resolved → Closed

**Invalid transitions tested (sample):**

- Open → Resolved, Closed
- In Progress → Open
- Resolved → In Progress, Cancelled
- Closed → Open, In Progress
- Cancelled → Open, In Progress

### Validators

Pydantic validation is exercised indirectly via integration tests (422 responses). No separate unit tests for schemas — boundary validation is thin and better tested through HTTP.

---

## API / Integration Tests

### Fixtures (`conftest.py`)

- `db_session` — in-memory SQLite, `Base.metadata.create_all`
- `client` — `TestClient(create_app())` with `get_db` overridden to test session
- `users` — Alice (Admin) + Bob (Agent)
- `open_ticket` — POST creates an Open ticket assigned to Bob

### State machine integration (`test_state_machine_integration.py`)

| Test | Asserts |
|------|---------|
| `test_full_valid_lifecycle` | Open → In Progress → Resolved → Closed (all 200) |
| `test_open_to_cancelled` | Open → Cancelled (200) |
| `test_in_progress_to_cancelled` | Open → In Progress → Cancelled (200) |
| `test_invalid_transitions_from_open_or_in_progress` | Skip-ahead, backward, Resolved → Cancelled → 409 `invalid_transition` |
| `test_no_transitions_from_closed` | All targets from Closed → 409 |
| `test_no_transitions_from_cancelled` | All targets from Cancelled → 409 |
| `test_status_cannot_be_changed_via_patch` | PATCH with `status: Closed` leaves status as Open |

### Ticket API (`test_ticket_api.py`)

| Test | Asserts |
|------|---------|
| `test_create_ticket_validation` | Title too short → 422 `validation_error` |
| `test_create_ticket_invalid_user` | `created_by: 9999` → 404 |
| `test_update_closed_ticket_rejected` | PATCH on Cancelled ticket → 409 `ticket_not_editable` |
| `test_comment_on_cancelled_rejected` | POST comment on Cancelled → 409 `comment_not_allowed` |
| `test_search_filter` | `?q=uniquesearchterm` finds ticket by title (case-insensitive) |
| `test_csv_export` | Export returns `text/csv` with header row and ticket data |

### Coverage matrix

| Area | Covered | Gap |
|------|---------|-----|
| Ticket CRUD happy path | Partial (create via fixture; get implicit) | Explicit GET/PATCH happy path test |
| Every valid transition | Yes (3 dedicated + lifecycle) | — |
| Invalid transitions | Yes (parametrized + terminal states) | Same-status no-op (Open → Open) |
| PATCH status bypass | Yes | — |
| Comment rules | Cancelled only | Resolved comment success; Closed comment 409 |
| CSV export | Content + content-type | Empty user (header only); special chars |
| List filters | Search (`q`) only | `status` and `priority` filter params |

---

## Edge Case Tests

Mapped from [requirements-analysis.md](requirements-analysis.md) edge cases:

| Edge case | Test coverage | Notes |
|-----------|---------------|-------|
| Skip-ahead transitions | `test_invalid_transitions_from_open_or_in_progress` | Open → Resolved, Open → Closed |
| Backward transitions | Same test | In Progress → Open; Resolved → In Progress |
| Reopen from terminal | `test_no_transitions_from_closed/cancelled` | Closed/Cancelled → any |
| Resolved → Cancelled | `test_invalid_transitions_from_open_or_in_progress` | Parametrized |
| Status via PATCH | `test_status_cannot_be_changed_via_patch` | Status unchanged |
| Edit on read-only | `test_update_closed_ticket_rejected` | Cancelled → 409 |
| Comment on terminal | `test_comment_on_cancelled_rejected` | Cancelled → 409 |
| Invalid user on create | `test_create_ticket_invalid_user` | 404 |
| Short title | `test_create_ticket_validation` | 422 |
| CSV creator scope | `test_csv_export` | Filters by `created_by` |
| Search case-insensitive | `test_search_filter` | `q` lowercase matches mixed-case title |
| Same-status no-op | **Not tested** | Open → Open should 409 |
| Whitespace-only comment | **Not tested** | Should 422 |
| Missing `created_by` on export | **Not tested** | Should 422 |
| Clear assignee (`assigned_to: null`) | `test_clear_assignee` | PATCH unassigns |
| CSV special-char quoting | **Not tested** | **Day 2:** description with `,` `"` `\n` — prove export round-trips via `csv.reader` |

Gaps above are candidates for follow-up tests if time permits.

---

## Day 2 — Planned integration tests

From smoke-test observations (2026-07-19); not failures, polish coverage:

### `test_csv_export_escapes_special_characters`

**Why:** Smoke test only hit seeded descriptions without commas, quotes, or newlines. `csv.writer` is used but never proven under nasty input.

**Setup:**
```python
description = 'Says "hello", world\nSecond line'
client.post("/api/tickets", json={
    "title": "CSV escape test ticket",
    "description": description,
    "priority": "Low",
    "created_by": users["alice"].id,
})
```

**Assert:**
- `GET /api/tickets/export?created_by={alice.id}` → 200
- Parse response body with `csv.reader`; find row by title
- `description` column equals original string exactly (no corruption, proper quoting)

**File:** `tests/test_ticket_api.py`

---

## Tests Not Covered (and why)

| Area | Why skipped | Mitigation |
|------|-------------|------------|
| **Frontend e2e** (Playwright/Cypress) | Time budget (~3 days solo); backend-heavy focus | Manual UI smoke: create ticket, edit, transition, comment, export CSV, verify error banners |
| **Pydantic schema unit tests** | Thin wrappers; integration 422 tests sufficient | Swagger validation failure spot-check |
| **Concurrency / race conditions** | Documented as known limitation (last-write-wins) | Not required for assessment scope |
| **Auth** | Out of scope | Acting-as selector tested manually |
| **Performance / load** | Out of scope for assessment data volume | SQLite adequate for demo |
| **Postgres-specific** | SQLite is default; schema designed to be portable | `data-model.md` migration notes |

### Manual smoke checklist (Swagger + browser)

- [ ] Full lifecycle: Open → In Progress → Resolved → Closed
- [ ] Invalid transition: Open → Resolved → 409 with allowed targets
- [ ] Invalid transition: Closed → In Progress → 409
- [ ] Create with empty title → 422
- [ ] Comment on Cancelled ticket → 409
- [ ] Restart server → data persists
- [ ] CSV export for seeded user downloads correct file
- [ ] UI: acting-as selector changes `createdBy` on new ticket
- [ ] UI: status buttons show only valid transitions
- [ ] UI: 409 transition rejection shows friendly banner message
