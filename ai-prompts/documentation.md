# Documentation

---

# Chat 7 — Tool workflow (Part A)
_Exported on 7/19/2026 at 21:24:00 GMT+5:30 from Cursor (3.12.17)_

---

**User**

Help me write tool-workflow.md — my AI workflow document. Draft it from these
real practices of mine; keep my first-person voice, no fluff:

- Primary tool: Cursor (chat + Agent mode + inline Cmd+K edits + project rules).
- Project context: .cursor/rules/*.mdc for durable conventions (stack, error
  shape, state-machine table), @file mentions of my own artifacts
  (requirements-analysis.md, api-contract.md) so generation is grounded in
  decisions I already made, spec paste block for one-off context.
- Requirement analysis: I paste the raw spec and make the AI interview ME with
  clarifying questions first, answer as product owner, then generate the
  analysis and challenge it for missed edge cases.
- Planning & design: artifacts in dependency order (requirements -> acceptance
  criteria -> data model -> API contract -> design/test strategy -> plan), each
  generated with the previous ones attached as context.
- Code generation: Agent mode, one bounded task per prompt, rules keep
  conventions consistent; I read every diff before accepting.
- Validating AI code: read + explain-back (if I can't explain it, I ask the AI
  to walk through it, then simplify), run it, test it, check against
  acceptance-criteria.md.
- Testing: AI drafts the test matrix from test-strategy.md; I verify the
  state-machine matrix is complete (every valid + invalid transition) and that
  tests fail when I break the code on purpose.
- Debugging: paste the actual error + relevant file references, ask for
  hypotheses ranked by likelihood, verify the fix, log it in debugging-notes.md.
- Code review: a dedicated review chat over the diff — correctness, security,
  consistency with api-contract.md; I record accepted/changed/rejected
  suggestions with reasons in code-review-notes.md.
- What I don't share: secrets/credentials (only .env.example is committed or
  pasted), personal data, anything from other projects/employers.
- Reuse in a real project: the rules files, the artifact-first sequence, and
  the prompt templates in ai-prompts/ are portable to any feature kickoff.

Structure it with one ## section per bullet above, in that order.

---

**Cursor**

Wrote `tool-workflow.md` in first-person voice with 11 sections: Primary tool, Project context, Requirement analysis, Planning & design, Code generation, Validating AI code, Testing, Debugging, Code review, What I don't share, Reuse in a real project.

---

**User**

yes (commit and export)

---

**Cursor**

Committed `tool-workflow.md` and appended this Chat 7 session to `ai-prompts/documentation.md`.

---

# Chat 8 — Candidate info and PR description
_Exported on 7/20/2026 at 10:13:00 GMT+5:30 from Cursor (3.12.17)_

---

## 8a — Draft submission artifacts

**User**

Using the repo as context, draft these files. Keep my first-person voice, specific and honest — no filler:

1. `candidate-info.md` — per the template: name Rakesh Singh, role, stack (Python/FastAPI + React), primary AI tool Cursor, project option Support Ticket Management System (backend-heavy), start/submission dates, short project summary, tools used, setup summary pointing at README.
2. `pr-description.md` — as if this repo were one PR: summary, features implemented (map to the Core acceptance criteria), technical changes (state-machine service, error-shape middleware, migrations/seed), database changes, testing done (35+ tests: unit + integration incl. full transition matrix; manual API + UI smoke tests in test-results.md), AI usage summary, known limitations (no auth, no pagination UI, single-user concurrency), future improvements.

Ask me for any personal details you don't know rather than inventing them.

**Cursor**

Drafted both files from repo evidence:

**`candidate-info.md`** — name, stack, Cursor, project option, 3-day summary, tools table, setup pointing at `README.md` + `database/setup-notes.md`. Start date **2026-07-19** from Day 1 artifacts. Flagged **role** and **submission date** for confirmation (placeholder: Software Engineer; submission 2026-07-20).

**`pr-description.md`** — PR-style write-up mapping all Core acceptance criteria, technical changes (state machine, error handlers, service layer, schemas, frontend, migrations/seed), DB migrations 001/002, **58 automated tests** (16 unit + 13 integration + 29 API) plus manual Swagger/UI/Playwright smoke from `test-results.md`, AI usage summary, known limitations, future improvements (including honest note that frontend code-review fixes were reviewed but not committed).

---

## 8b — Commit and export

**User**

Commit: `docs: candidate info and PR description`. Export → `ai-prompts/documentation.md`.

**Cursor**

Committed `candidate-info.md`, `pr-description.md`, and this export.

**Commit:** `docs: candidate info and PR description`

---

## Outcome

| Artifact | Status |
|----------|--------|
| `candidate-info.md` | Filled — pending user confirmation of role and submission date |
| `pr-description.md` | Complete PR-style summary for submission |
| `ai-prompts/documentation.md` | Chat 8 appended |

---

# Chat 9 — Reflection interview and AI usage summary
_Exported on 7/20/2026 at 10:22:00 GMT+5:30 from Cursor (3.12.17)_

---

## 9a — Eight-question reflection interview

**User**

Interview me for `reflection.md`: ask me 8 short questions, one at a time, about what I built, where AI helped most, where it was wrong (use `debugging-notes.md` and `code-review-notes.md` for real examples), how I validated output, and what I'd improve. Then write `reflection.md` from my answers using the template sections (What I Built / How I Used AI / What AI Helped With Most / What AI Got Wrong / How I Validated AI Output / What I Would Improve Next / Reusable Workflow). Also write `final-ai-usage-summary.md`: a one-page lifecycle map — phase → how AI was used → artifact/chat that proves it (link the `ai-prompts/` files and key commits).

**Cursor**

Conducted an 8-question interview (one at a time). Wrote both artifacts in the candidate's first-person voice from their answers.

**Interview topics covered:**
1. What I built — state machine as the strongest deliverable
2. How I used AI — artifacts-first, Chat vs Agent, frontend accepted in larger chunks
3. What AI helped with most — transition test matrix, contract→endpoints chain, seed/migrations
4. What AI got wrong — CSV formula injection (`70d7715`), unescaped `LIKE` wildcards (`677475a`)
5. How I validated — break-the-tests check, 27 API + 14 UI smoke, README dry run, evidence before ticking criteria
6. What I'd improve next — commit frontend review fixes, reconcile `api-contract.md`, Playwright over manual UI
7. Reusable workflow — artifact order, `.cursor/rules`, failure-scenario gate; avoid big frontend generations
8. Closing — warning (edges fail quietly) + habit (capture evidence as you go)

**`reflection.md`** — all seven template sections plus closing advice for teammates.

**`final-ai-usage-summary.md`** — 10-phase lifecycle table linking `ai-prompts/*.md`, key commits, conventions, honest gaps, final test bar (58 passed).

---

## 9b — Commit and export

**User**

Commit: `docs: reflection and final AI usage summary`. Export → `ai-prompts/documentation.md`.

**Cursor**

Committed `reflection.md`, `final-ai-usage-summary.md`, and this export.

**Commit:** `docs: reflection and final AI usage summary`

---

## Outcome

| Artifact | Status |
|----------|--------|
| `reflection.md` | Complete — first-person reflection from 8-question interview |
| `final-ai-usage-summary.md` | Complete — one-page AI lifecycle map |
| `ai-prompts/documentation.md` | Chat 9 appended |


