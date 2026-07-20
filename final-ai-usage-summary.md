# Final AI Usage Summary

One-page map of how Cursor was used across the assessment lifecycle. **Primary tool:** Cursor (Chat + Agent + `.cursor/rules/*.mdc`). **Project:** Support Ticket Management System (backend-heavy). **Dates:** 2026-07-19 → 2026-07-20.

---

| Phase | How AI was used | Artifact / evidence |
|-------|-----------------|---------------------|
| **1. Requirements** | Pasted raw spec; AI interviewed me as product owner (clarifying questions first); generated and challenged `requirements-analysis.md` for missed edge cases | [`ai-prompts/planning.md`](ai-prompts/planning.md) · commits `811c837`, `42848a3` |
| **2. Acceptance criteria** | Generated testable checkboxes from requirements; later audited and ticked only with evidence | [`acceptance-criteria.md`](acceptance-criteria.md) · commits `7a2acd9`, `7292e03` |
| **3. Design** | Data model + API contract + UI flow + test strategy in dependency order, each `@`-mentioning prior artifacts | [`ai-prompts/design.md`](ai-prompts/design.md) · commits `33ac56e`, `7a19123` |
| **4. Planning** | Implementation plan, tool workflow doc, Day 1–3 task breakdown | [`ai-prompts/planning.md`](ai-prompts/planning.md) · [`tool-workflow.md`](tool-workflow.md) · commits `4190804`, `8dcb891` |
| **5. Backend implementation** | Agent mode, bounded prompts: scaffold → models/migration/seed → state machine service → endpoints; rules enforced error shape and transition table | [`ai-prompts/implementation.md`](ai-prompts/implementation.md) · commits `b0ef464`, `57e1066`, `b4f6898` |
| **6. Frontend implementation** | Multi-file React generation (list, detail, create, acting-as context); less line-by-line review than backend | [`ai-prompts/implementation.md`](ai-prompts/implementation.md) (Chat 8) · in initial `b4f6898` era |
| **7. Testing** | AI drafted transition matrix tests; manual Swagger (27/27), UI smoke (14/14), README dry run, Playwright banner checks; gap-closing integration tests | [`ai-prompts/testing.md`](ai-prompts/testing.md) · [`test-results.md`](test-results.md) · commits `fd2fd97`, `18b3bc2`, `74a9e67`, `b36f458`, `a8fb181` |
| **8. Debugging** | Operational issues logged (port conflicts); smoke observations (timestamp precision, CSV quoting) drove follow-up tests | [`ai-prompts/debugging.md`](ai-prompts/debugging.md) · [`debugging-notes.md`](debugging-notes.md) · commit `9992758` |
| **9. Code review** | Strict AI backend review (21 findings); triage with concrete failure scenarios; 19 one-commit-per-fix implementations | [`ai-prompts/code-review.md`](ai-prompts/code-review.md) · [`code-review-notes.md`](code-review-notes.md) · [`review-fixes.md`](review-fixes.md) · commits `7eba88c`, `d9f03ad`…`5aec259`, `d93174e` |
| **10. Submission docs** | Drafted candidate info + PR description from repo state; reflection interview (this doc) | [`ai-prompts/documentation.md`](ai-prompts/documentation.md) · commits `815df92` · [`candidate-info.md`](candidate-info.md) · [`pr-description.md`](pr-description.md) · [`reflection.md`](reflection.md) |

---

## Key conventions (`.cursor/rules/`)

| Rule file | What it locked in |
|-----------|-------------------|
| `00-project-context.mdc` | Stack, layout, assessment constraints |
| `20-state-machine.mdc` | Transition table; status **only** via `POST …/status`; 409 on invalid |

These rules meant I reviewed AI output for logic, not for re-explaining conventions every prompt.

---

## Highest-value AI contributions

1. **State-machine test matrix** — full valid/invalid transition coverage in minutes (`tests/test_state_machine_unit.py`, `tests/test_state_machine_integration.py`).
2. **Contract-first endpoints** — `api-contract.md` → routers/schemas with consistent `{"error": {…}}` envelope.
3. **Review pass** — surfaced CSV formula injection and unescaped `LIKE` wildcards; fixed with regression tests.

## Known honest gaps

- Frontend code-review fixes documented but **not committed** (see `reflection.md`).
- `api-contract.md` not yet updated for `extra="forbid"` on PATCH `status` → 422.
- UI smoke is manual, not yet a repeatable Playwright suite.

---

## Final test bar

`venv/bin/python -m pytest -q` → **58 passed** · Manual evidence in [`test-results.md`](test-results.md) · All Core criteria ticked in [`acceptance-criteria.md`](acceptance-criteria.md).
