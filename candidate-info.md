# Candidate Information

## Name

Rakesh Singh

## Role

Software Engineer

## Stack

- **Backend:** Python, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, SQLite (designed to swap to Postgres via `DATABASE_URL`)
- **Frontend:** React, Vite
- **Testing:** pytest, httpx `TestClient`
- **Tooling:** Alembic migrations, uvicorn, npm/Vite build

## Primary AI Tool

**Cursor** — Chat for planning and review-only passes; Agent mode for bounded implementation; `.cursor/rules/*.mdc` for durable conventions (stack, error shape, state-machine table); `@file` references to my own artifacts (`api-contract.md`, `requirements-analysis.md`, etc.).

## Project Option

**Support Ticket Management System** (backend-heavy option) — internal ticket app with enforced lifecycle, comments, search/filter, JWT authentication (stretch), and token-scoped CSV export. Seeded users log in via the UI; role rules gate status changes and Requester edit scope.

## Dates

| | Date |
|---|------|
| **Start** | 2026-07-19 |
| **Submission** | 2026-07-20 |

## Project Summary

I built a small support ticket system where seeded users log in and create/progress tickets through a strict state machine (Open → In Progress → Resolved → Closed, with Cancelled as an alternate exit from Open/In Progress). The backend owns all business rules — status changes go only through `POST /api/tickets/{id}/status`, edits are allowed only in Open/In Progress, and comments are blocked on Closed/Cancelled. JWT auth (stretch) protects mutations; `created_by` is always derived from the token. The React UI covers login, list/search/filter, create, detail (edit, role-aware status actions, comments), and CSV export scoped to the logged-in user. I grounded implementation in written artifacts first (`requirements-analysis.md`, `api-contract.md`, `acceptance-criteria.md`), then hardened with pytest (91 tests), post-JWT API smoke, and a backend code review pass that produced 19 targeted fix commits.

## Tools Used

| Category | Tools |
|----------|-------|
| IDE / AI | Cursor (Agent, Chat, inline edits, project rules) |
| Backend | FastAPI, SQLAlchemy 2.0, Alembic, Pydantic, uvicorn |
| Frontend | React, Vite |
| Database | SQLite (`app.db`), Alembic migrations |
| Testing | pytest; manual Swagger (`/docs`); browser UI smoke; Playwright spot-checks for error banners |
| Docs / process | Markdown artifacts, `ai-prompts/` chat exports, `tool-workflow.md` |

## Setup Summary

Clone the repo and follow **`README.md`** at the project root:

1. Python 3.11+ venv → `pip install -r requirements.txt`
2. `cp .env.example .env` (defaults work for local SQLite)
3. `alembic upgrade head` → `python -m src.backend.seed`
4. `uvicorn src.backend.app.main:app --reload --port 8000`
5. `cd src/frontend && npm install && npm run dev` → http://localhost:5173 (login with seeded email + `Password123`)

Run tests: `pytest -v` (or `venv/bin/python -m pytest -q`) from the project root with the venv active — **91 tests** as of submission.

More detail on schema, migrations, and reset: `database/setup-notes.md`.
