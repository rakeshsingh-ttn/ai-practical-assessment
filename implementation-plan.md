# Implementation Plan

## Overview

Three-day solo build of the Support Ticket Management System: a FastAPI + SQLite backend with an enforced status state machine, a React (Vite) frontend with acting-as user context, and pytest integration tests. **Core features first; Stretch only if time remains.**

**Current state (end of Day 1 planning):** Backend, frontend, migrations, seed data, and ~34 passing tests already exist from an initial AI-assisted build. Day 1 remaining focuses on completing planning artifacts, verifying the backend via Swagger smoke tests, and fixing any issues found. Day 2 hardens tests and validates the frontend against `acceptance-criteria.md`. Day 3 is review, documentation, artifact completion, and submission — with a buffer for surprises.

**Definition of done:** Every Core checkbox in `acceptance-criteria.md` ticked; `pytest -v` green; README works from a clean clone; all required `.md` artifacts committed; prompt history exported to `ai-prompts/`.

---

## Task Breakdown

### Day 1 (remaining) — Backend verified, planning complete

| # | Task | Est. | Acceptance / test link |
|---|------|------|------------------------|
| 1.1 | Finish planning artifacts: `requirements-analysis.md`, `acceptance-criteria.md`, `data-model.md`, `api-contract.md`, `design-notes.md`, `ui-flow.md`, `test-strategy.md`, `implementation-plan.md` | 2h | Documentation section of acceptance criteria |
| 1.2 | Verify FastAPI scaffold: health endpoint, CORS, error handlers, `.env.example` | 0.5h | README runs from scratch (partial) |
| 1.3 | Verify models + Alembic migration + idempotent seed (4 users, 12 tickets, 8 comments) | 0.5h | View all tickets from DB; data survives restart |
| 1.4 | Verify state machine service (`ALLOWED_TRANSITIONS`, `can_transition`, `transition`) | 0.5h | Status only via valid transitions |
| 1.5 | Verify all API endpoints incl. CSV export; fix any contract mismatches | 1.5h | api-contract.md matches implementation |
| 1.6 | Manual Swagger smoke test: full lifecycle, invalid transitions (409), validation (422), comment on cancelled (409), CSV download, restart persistence | 1h | Manual smoke checklist in test-strategy.md |
| 1.7 | Log any failures in `debugging-notes.md`; commit fixes | 0.5h | — |
| 1.8 | Export Day 1 chats to `ai-prompts/planning.md` and `ai-prompts/design.md` | 0.5h | Assessment evidence |

**Day 1 remaining total: ~7h**

---

### Day 2 — Tests first, then frontend validation

| # | Task | Est. | Acceptance / test link |
|---|------|------|------------------------|
| 2.1 | Run existing test suite; confirm 34+ tests green | 0.5h | All tests green |
| 2.2 | Add missing integration tests from test-strategy gaps: same-status no-op (Open → Open), status/priority filter params, clear assignee (`assigned_to: null`) | 1.5h | Testing section of acceptance criteria |
| 2.3 | Verify unit test matrix covers all valid transitions + terminal states | 0.5h | Unit: transition matrix |
| 2.4 | Frontend: verify ticket list (table columns, search, status/priority filters, acting-as selector) | 1h | Core: list, search/filter, acting-as |
| 2.5 | Frontend: verify create ticket form (inline 422 errors, `createdBy` from selector) | 0.5h | Create via UI |
| 2.6 | Frontend: verify ticket detail (edit Open/In Progress, read-only Resolved/Closed/Cancelled, status buttons for valid transitions only) | 1.5h | Update fields; status transitions; disabled UI |
| 2.7 | Frontend: verify comments (add on Open/In Progress/Resolved; blocked on Closed/Cancelled; 409 banner) | 0.5h | Add comments; 409 comment on closed |
| 2.8 | Frontend: verify CSV export button (creator-only scope, download) | 0.5h | CSV export of self-created tickets |
| 2.9 | Frontend: verify error states (422 inline, 404/409 banner, friendly transition messages) | 0.5h | Error Handling section |
| 2.10 | End-to-end pass: tick every checkbox in `acceptance-criteria.md`; fix gaps | 1.5h | Full acceptance criteria |
| 2.11 | Write `test-results.md` with pytest output summary | 0.5h | Documentation |
| 2.12 | Export Day 2 chats to `ai-prompts/testing.md` and `ai-prompts/implementation.md` | 0.5h | Assessment evidence |

**Day 2 total: ~9h**

---

### Day 3 — Review, artifacts, submission (keep buffer)

| # | Task | Est. | Acceptance / test link |
|---|------|------|------------------------|
| 3.1 | AI code review pass over full diff; record findings in `code-review-notes.md` | 1.5h | Reviewability |
| 3.2 | Apply accepted review fixes; log rejected suggestions with reasons in `review-fixes.md` | 1h | — |
| 3.3 | Write `tool-workflow.md` (Part A — AI workflow document) | 1h | Assessment Part A |
| 3.4 | Fill `candidate-info.md` | 0.25h | Submission requirement |
| 3.5 | README dry run from clean clone (fresh venv, migrate, seed, run backend + frontend) | 1h | README runs from scratch |
| 3.6 | Update `database/setup-notes.md` if dry run reveals gaps | 0.5h | Schema/migrations documented |
| 3.7 | Complete remaining artifacts: `debugging-notes.md`, `reflection.md`, `pr-description.md`, `final-ai-usage-summary.md` | 1.5h | Assessment artifacts |
| 3.8 | Prompt-history cleanup: verify all chats exported to correct `ai-prompts/` files | 0.5h | Assessment evidence |
| 3.9 | Final `pytest -v` + quick UI smoke | 0.5h | All tests green |
| 3.10 | **Buffer** — unexpected fixes, push to remote, submission form | 2h | M5 submitted |

**Day 3 total: ~9.75h (incl. 2h buffer)**

---

## Milestones

| Milestone | Target | Done when |
|-----------|--------|-----------|
| **M1 — Backend demoable** | End of Day 1 | All endpoints work in Swagger; state machine rejects invalid transitions (409); data persists across restart; seed data loads |
| **M2 — Tests green** | Morning Day 2 | `pytest -v` passes; state-machine integration tests cover every valid transition and terminal-state rejections; known gaps filled or documented |
| **M3 — Frontend complete** | End of Day 2 | All three screens work; acting-as selector, search/filter, status buttons, comments, CSV export, error states verified; Core acceptance criteria ticked |
| **M4 — Artifacts complete** | Mid Day 3 | All required `.md` files filled; README dry run succeeds; code review and reflection written; prompt history exported |
| **M5 — Submitted** | End of Day 3 | Repo pushed; submission form completed; buffer unused or consumed for last-minute fixes only |

---

## AI Usage Plan

Prompt history is exported per chat to the `ai-prompts/` folder. Each phase uses a focused prompt with `@` references to prior artifacts.

| Lifecycle phase | Prompt location | Inputs attached | Output artifacts |
|-----------------|-----------------|-----------------|------------------|
| **Planning** | `ai-prompts/planning.md` | Raw spec, PO answers | `requirements-analysis.md`, `acceptance-criteria.md`, `implementation-plan.md` |
| **Design** | `ai-prompts/design.md` | `@requirements-analysis.md` | `data-model.md`, `api-contract.md`, `design-notes.md`, `ui-flow.md`, `test-strategy.md` |
| **Implementation** | `ai-prompts/implementation.md` | `@design-notes.md`, `@api-contract.md`, `@data-model.md` | `src/backend/`, `src/frontend/`, commits per feature |
| **Testing** | `ai-prompts/testing.md` | `@test-strategy.md`, `@acceptance-criteria.md` | `tests/`, `test-results.md` |
| **Debugging** | `ai-prompts/debugging.md` | Error output + relevant file `@` refs | `debugging-notes.md`, fix commits |
| **Code review** | `ai-prompts/code-review.md` | Diff or `@` changed files | `code-review-notes.md`, `review-fixes.md` |
| **Documentation** | `ai-prompts/documentation.md` | Completed project state | `tool-workflow.md`, `reflection.md`, `final-ai-usage-summary.md` |

**Prompt style:** Agent mode for file creation; one bounded task per prompt; correct AI mistakes in the same chat (wrong-then-corrected is evidence); small commits with meaningful messages.

---

## Risks

| Risk | Likelihood | Impact |
|------|------------|--------|
| **Time overrun** — 3 days is tight for full stack + artifacts | Medium | High |
| **Scope creep into Stretch** (auth, Postgres, e2e tests, delete) | Medium | High |
| **AI-generated code I don't fully understand** — especially state machine and SQLAlchemy session handling | Medium | Medium |
| **Last-minute setup breakage** — README steps fail on clean clone (venv paths, migration order, CORS) | Medium | High |
| **Test gaps** — acceptance criteria require cases not yet automated (same-status no-op, filter params) | Low | Medium |
| **Frontend error handling gaps** — 422 inline vs 409 banner not wired consistently | Low | Medium |

---

## Mitigation

| Risk | Mitigation |
|------|------------|
| Time overrun | **Core before Stretch always.** If behind on Day 2 afternoon, skip optional test gaps and document in `test-strategy.md`. Day 3 buffer is for submission only. |
| Scope creep | Refer every feature request to `acceptance-criteria.md` Core section. Stretch items (auth, Postgres, e2e) are explicitly out of scope. |
| Unreviewed AI code | Read every diff before accepting. For each non-trivial file, add an entry to `code-review-notes.md` explaining what it does. If I can't explain it, ask AI to walk through it and simplify. |
| Setup breakage | **README dry run on Day 3 morning** from a clean clone. Fix immediately; update `database/setup-notes.md`. |
| Test gaps | Day 2 morning dedicated to tests-first. Prioritise state-machine matrix (mandatory) over nice-to-have edge cases. |
| Frontend errors | Cross-check against `ui-flow.md` error state table. Manual smoke on Day 2 afternoon before ticking acceptance criteria. |

**Commit discipline:** Small commits with meaningful messages (`feat:`, `fix:`, `docs:`, `test:`). Every fix from a failed smoke test gets its own `fix:` commit — ready-made `debugging-notes.md` entries.
