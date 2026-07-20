# Support Ticket Management System

Internal support ticket app — FastAPI backend, React (Vite) frontend, SQLite database, JWT authentication.

## Prerequisites

- Python 3.11+
- Node.js 18+ (for frontend)

## Backend setup

From the project root:

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment (optional — defaults work for local dev)
cp .env.example .env

# Run database migrations
alembic upgrade head

# Seed sample data
python -m src.backend.seed

# Start the API server
uvicorn src.backend.app.main:app --reload --port 8000
```

- API: http://localhost:8000
- Swagger docs: http://localhost:8000/docs
- Health check: http://localhost:8000/api/health

## Frontend setup

```bash
cd src/frontend
npm install
npm run dev
```

- App: http://localhost:5173 (redirects to login if not authenticated)

## Authentication

The UI uses a login screen. All mutating API calls require a JWT bearer token.

**Seeded users** (all share the same default password):

| Email | Role |
|-------|------|
| `alice@example.com` | Admin |
| `bob@example.com` | Agent |
| `carol@example.com` | Manager |
| `dave@example.com` | Requester |

**Default password:** `Password123`

```bash
# Obtain a token
curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"Password123"}'

# Use on protected endpoints
curl -s http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <access_token>"
```

JWT settings in `.env` (see `.env.example`): `JWT_SECRET`, `JWT_ALGORITHM`, `JWT_EXPIRE_MINUTES`.

Role rules: only Admin/Agent/Manager can change ticket status; Requesters can create, edit, and comment on **their own** tickets only. CSV export requires auth and is scoped to the logged-in user. Ticket reads remain public by deliberate choice for this demo — see [api-contract.md](api-contract.md#authentication).

## Run with Docker

Prerequisites: Docker and Docker Compose.

From the project root:

```bash
docker compose up --build
```

- App: http://localhost:8080
- API (proxied): http://localhost:8080/api/health
- Swagger UI: http://localhost:8080/docs

On first start the backend runs `alembic upgrade head` and seeds sample data if the database is empty. SQLite is stored in the `ticket-data` Docker volume (`/data/app.db` in the backend container).

Stop and remove containers (data volume is kept):

```bash
docker compose down
```

Remove containers and the database volume:

```bash
docker compose down -v
```

The manual Python/Node setup above is unchanged and does not require Docker.

## Tests

```bash
# From project root, with venv activated
pytest -v
```

**91 tests** — includes auth (login, 401/403), role permissions, export auth scoping, state machine, and ticket API coverage.

## Project layout

```
src/backend/app/
  main.py           # App factory, CORS, router registration
  config.py         # pydantic-settings (.env, JWT)
  database.py       # SQLAlchemy engine + get_db dependency
  auth/             # JWT, passwords, permissions, get_current_user
  routers/          # HTTP endpoints (auth, health, users, tickets)
  services/         # Business logic
  models/           # SQLAlchemy ORM entities
  schemas/          # Pydantic request/response models
src/frontend/src/
  pages/LoginPage.jsx   # Login screen (replaces acting-as selector)
  api/client.js         # JWT storage + Authorization header
```
