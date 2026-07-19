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
