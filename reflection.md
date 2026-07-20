# Reflection

## What I Built

I delivered a working support-ticket system end to end: a FastAPI backend (SQLAlchemy + Alembic + SQLite) with ticket CRUD, comments, search/filter, CSV export, and an enforced status state machine; a React frontend with list/detail/create flows and an acting-as user selector standing in for auth; plus migrations, seed data, and 58 passing tests (35+ from the initial build, grown through review fixes and smoke follow-ups).

The part I'm most confident about is the state machine. I kept it in one isolated service module with the transition table as data, so there's exactly one enforcement point — the status endpoint — and PATCH can never touch status. It's covered by unit tests over the full transition matrix and integration tests through the API (valid transitions succeed, invalid ones return 409 with the allowed moves listed), and the UI enforces it independently by only rendering valid action buttons — terminal states get none. That two-layer design survived both the automated suite and manual API/UI smoke testing without a single failure, which is why I'd back it in a real review.

## How I Used AI

In practice I really did work artifacts-first: requirements, acceptance criteria, data model, and API contract were generated and committed before any code, and I attached those files with `@`-mentions to every implementation prompt so the code was generated against decisions I'd already made, not the model's guesses. I planned each day's prompt sequence in advance rather than improvising, which kept sessions bounded — one chat per concern (schema, state machine, endpoints) instead of one giant "build the app" prompt.

I used plain Chat for analysis — including making the AI interview me with clarifying questions on the spec before writing the requirements doc — and Agent mode for anything that touched files; project rules in `.cursor/rules/` carried the conventions (error shape, transition table, layering) so I didn't have to restate them every prompt.

Where reality diverged from the ideal workflow: the frontend came out in bigger multi-file generations than I'd planned, so there I reviewed less line-by-line up front and leaned more on running the app, manual smoke testing, and a dedicated code-review pass afterwards to catch what I'd accepted too quickly. For backend code I read every diff before accepting, and for the state-machine service I had the AI explain the module back to me and simplified it until I could explain it myself.

## What AI Helped With Most

The single biggest saving was the state-machine test matrix. Because the transition table lived in one rules file, I could ask for integration tests covering every valid transition and every invalid one — including out of the terminal states — and got a systematic suite in minutes that I'd have half-skipped by hand out of tedium; that's most of the tests that now gate every change.

The second was the API-contract-to-endpoints chain: I had AI draft `api-contract.md` first (request/response examples, validation rules, the single error shape, 422/404/409 policy), then generated the routers and Pydantic schemas from that contract, so all ten endpoints came out consistent on the first pass — same error envelope everywhere, no drift between docs and code to reconcile later.

Honorable mention: the mechanical layer nobody enjoys — Alembic wiring and a realistic seed script (4 users, 12 tickets spread across every status and priority, comments) — which made every later test and demo instantly meaningful.

## What AI Got Wrong

The one that mattered most was **CSV formula injection** in the export. The AI-generated export wrote ticket fields into cells verbatim, so a ticket titled `=HYPERLINK(...)` or starting with `+`, `-`, or `@` would execute as a formula the moment someone opened the export in Excel — user-controlled input becoming executable, in the one feature explicitly meant to leave the system. Nothing in normal testing catches it because the CSV is "valid"; it only surfaced when I ran a security-focused review pass over the AI's code and specifically asked about export risks. The fix was escaping formula-leading characters on write, plus a regression test that exports a hostile title and asserts it comes back inert (`70d7715`).

The second was **search**: `q` went into a SQL `LIKE` unescaped, so searching `100%` silently matched everything — wrong results with a 200 status, the worst kind of bug. Caught it by throwing edge-case inputs at the filter during review, fixed it by escaping `%` and `_` before building the pattern, and added a test with wildcard characters in the query (`677475a`).

Both taught me the same lesson: AI code fails quietly at the boundaries — it passes the happy path and the demo — so my review effort now goes to inputs the feature was never demoed with.

A separate gap: the **frontend review pass** found real issues (documented in `code-review-notes.md` from the frontend session), but those fixes never landed in the repo. A documented-but-unfixed finding is worse than an unknown one.

## How I Validated AI Output

My rule was that pytest passing meant the code agreed with the tests — not that the tests were right — so everything got a second, independent check. For the state machine I inverted that dependency once: I deliberately broke the transition table (allowed Open → Resolved) and confirmed the matrix tests actually failed before trusting green as a signal.

Beyond that, nothing got ticked in `acceptance-criteria.md` without recorded evidence: a **27-check manual smoke test** through the API covering every criterion reachable over HTTP — including killing and restarting the server to prove persistence, and confirming invalid transitions came back as 409s with the standard error shape rather than stack traces — then a **14-check browser pass** where I verified in the network tab that the inline form errors were real backend 422s and not browser validation, walked a ticket through its full lifecycle in the UI, checked terminal-state tickets were properly read-only, and finished with a clean console. The last gate was a **fresh clone into `/tmp`** following the README word for word, because "works on my checkout" is the classic AI-assisted failure.

My minimum bar for "done" ended up being: an automated test, plus at least one manual or adversarial check documented in `test-results.md`, plus the criterion ticked against that evidence — code merely existing and running once never counted.

## What I Would Improve Next

**First:** commit the frontend review fixes. The review pass found real issues and they're documented, but the fixes never landed — and a documented-but-unfixed finding is worse than an unknown one, because the repo now proves I knew. Closing that loop (or explicitly recording the ones I'm consciously deferring, with reasons) ranks first because it's about the integrity of work I've already claimed, not new scope.

**Second:** reconcile `api-contract.md` with actual behavior after I tightened the schemas with `extra="forbid"` — the contract was the source the endpoints were generated from, and the whole value of an artifact-first workflow dies if the artifact is allowed to drift from the code; it's an hour of work that protects the credibility of every other document.

**Third:** replace the manual browser smoke test with a small Playwright suite covering the same 14 checks — the manual pass was solid evidence once, but it's not repeatable, and the lifecycle walk (create → transition → comment → terminal-state lockout) is exactly what will silently break under future changes.

I'd deliberately not spend the day on pagination UI or timestamp polish: both are real but neither threatens correctness or the claims the repo already makes, and adding features while known review findings sit unfixed would be the wrong order.

## Reusable Workflow

**Three things come with me without hesitation.**

First, the **artifact order**: requirements → acceptance criteria → data model → API contract before code, with each generation prompt `@`-mentioning the earlier artifacts — it turned the AI from guessing into implementing decisions I'd already made, and it's why ten endpoints came out consistent on the first pass.

Second, **`.cursor/rules`** as the home for durable conventions — the transition table, the error envelope, the layering rules lived there once instead of being restated in every prompt, so I never had to review for convention drift, only for logic.

Third, the **failure-scenario gate** on review findings: before accepting any AI review finding I asked "what concrete input or sequence makes this break?" — it cleanly separated the real issues (formula injection, the LIKE wildcard bug) from plausible-sounding noise, and it's the cheapest quality filter I've ever used.

**The one I wouldn't repeat:** letting the frontend come out in big multi-file generations. It felt fast, but I accepted more code per decision than I could genuinely review, and the cost surfaced later as a heavier review pass and findings I ran out of time to fix — the backend's rhythm of one bounded prompt, one readable diff, one commit was slower per hour but faster per feature. Next project, UI gets the same discipline as the API.

**If someone on my team were starting this same take-home tomorrow:**

- **Warning:** AI code fails quietly at the edges — everything you demo will work, and the bugs will be sitting in the inputs you never demoed, so spend your review effort where the happy path isn't.
- **Habit:** capture evidence as you go — export the chat and commit the moment a piece works, because in this exercise the prompt history and commit trail are the deliverable, and they're the one thing you can't honestly reconstruct on submission day.
