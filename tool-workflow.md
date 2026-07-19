# Tool Workflow

How I use AI-assisted development for this assessment and how I'd carry the same habits into a real project.

## Primary tool: Cursor

I use **Cursor** as my primary tool — not a one-off chatbot, but an IDE-integrated assistant:

- **Chat** for planning, analysis, and discussion-only steps.
- **Agent mode** when I need files created or edited across the repo.
- **Inline Cmd+K edits** for small, local changes inside a single file.
- **Project rules** (`.cursor/rules/*.mdc`) so conventions persist across every new chat without re-pasting context.

I stay in Agent mode for bounded implementation tasks; plain chat is fine when I'm thinking through requirements or reviewing a design.

## Project context

I don't rely on chat memory. I make context durable and attachable:

- **`.cursor/rules/*.mdc`** — stack, error JSON shape, state-machine transition table, backend/frontend/testing conventions. These apply automatically in every session.
- **`@file` mentions** — I attach my own artifacts (`requirements-analysis.md`, `api-contract.md`, `data-model.md`, etc.) so generation is grounded in decisions I already made, not re-invented each time.
- **Spec paste block** — for one-off context or the start of a new chat, I paste the raw project spec from `day1-cursor-prompts.md` so the AI knows the full scope.

If the AI drifts from a decision in an artifact, I point it at the file rather than arguing from memory.

## Requirement analysis

I don't let the AI jump straight to code or docs. My sequence:

1. Paste the raw spec.
2. Ask the AI to **interview me** as a senior engineer would a product owner — numbered clarifying questions, no analysis yet.
3. Answer as product owner (acting-as user, enum values, edit/comment rules, no delete, etc.).
4. Generate `requirements-analysis.md` from those answers.
5. Run a **challenge pass** — ask what's missing around the state machine, comments, CSV export, concurrency. Add only genuinely useful edge cases.

The Q&A exchange is evidence that I drove the requirements, not just accepted the AI's first draft.

## Planning & design

Artifacts are produced in **dependency order**, each built with the previous ones attached:

```
requirements-analysis.md
  → acceptance-criteria.md
  → data-model.md + api-contract.md
  → design-notes.md + ui-flow.md + test-strategy.md
  → implementation-plan.md
```

I use `@requirements-analysis.md` when writing acceptance criteria, `@api-contract.md` when writing design notes, and so on. This keeps the API contract, schema, UI flows, and test plan aligned — one source of truth per concern.

## Code generation

For implementation I use **Agent mode, one bounded task per prompt**:

- "Scaffold FastAPI with health endpoint" — not "build the entire backend."
- "Implement the state machine service" — its own commit.
- "Wire up ticket endpoints per api-contract.md" — separate step.

Project rules keep conventions consistent (thin routers, single error shape, status only via dedicated endpoint). **I read every diff before accepting** — I don't auto-apply blind. If a change touches the state machine or error handling, I cross-check against `.cursor/rules/20-state-machine.mdc` and `api-contract.md`.

## Validating AI code

I don't trust green AI output until I've verified it myself:

1. **Read** the generated code.
2. **Explain-back** — if I can't explain what a function does in plain language, I ask the AI to walk through it, then simplify until I understand it.
3. **Run it** — start the server, hit the endpoint, open the UI.
4. **Test it** — `pytest -v` for backend; manual smoke for UI flows.
5. **Check against `acceptance-criteria.md`** — tick boxes only when I've actually verified the behaviour.

If tests pass but I don't understand the code, that's a fail — not a pass.

## Testing

I let AI draft the test matrix from `test-strategy.md`, but I own completeness:

- **State-machine matrix** — every valid transition must succeed; representative invalid transitions (skip-ahead, backward, terminal states) must return 409. I verify the parametrized cases cover the full table.
- **Break-on-purpose** — I temporarily break `can_transition` or remove a 409 handler and confirm tests fail for the right reason. If they still pass, the test isn't testing anything.
- **Integration over mocks** — tests run against the real FastAPI app with in-memory SQLite, not mocked HTTP or DB.

Gaps I accept (no frontend e2e) are documented in `test-strategy.md`, not silently ignored.

## Debugging

When something breaks, I don't guess — I give the AI evidence:

1. Paste the **actual error** (traceback, HTTP response body, console output).
2. Attach **relevant file references** (`@ticket_status.py`, `@conftest.py`).
3. Ask for **hypotheses ranked by likelihood**, not a single shot fix.
4. Apply the fix, re-run, confirm.
5. Log the issue and resolution in `debugging-notes.md` — especially wrong-then-corrected exchanges; those are strong assessment evidence.

I fix in the same chat where the bug appeared; I don't delete and retry silently.

## Code review

I run a **dedicated review chat** over the diff (or `@` the changed files) before calling a feature done:

- Correctness — does it match `api-contract.md` and the state machine table?
- Security — no secrets, no unsafe patterns.
- Consistency — error shape, layering, naming.

I record outcomes in `code-review-notes.md`:

- **Accepted** — what I agreed with and why.
- **Changed** — what I modified after review.
- **Rejected** — what I declined and why.

Review is not rubber-stamping AI output.

## What I don't share

I treat the chat as untrusted for secrets:

- **No secrets or credentials** — API keys, tokens, passwords. Only `.env.example` is committed or pasted into chat; real values stay in gitignored `.env`.
- **No personal data** — real names, emails, or identifiers beyond seeded demo data.
- **Nothing from other projects or employers** — this repo and its prompts are self-contained.

If a secret accidentally appears in chat or code, I remove it, rotate if needed, and note the lesson in `tool-workflow.md` or `debugging-notes.md`.

## Reuse in a real project

This workflow is portable beyond the assessment:

| Asset | Reuse |
|-------|-------|
| **`.cursor/rules/*.mdc`** | Drop into any repo — adapt stack, error shape, and domain rules (e.g. state machine, API conventions). |
| **Artifact-first sequence** | requirements → acceptance criteria → contract → design → plan → implement → test. Works for any feature kickoff. |
| **`ai-prompts/` templates** | Planning, design, implementation, testing, debugging, code-review, documentation — copy and adapt per phase. |

The habit that matters most: **decisions live in files, not in chat history.** Rules and `@` artifacts make every new session productive without starting from zero.
