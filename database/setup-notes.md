# Database Setup Notes

## DB choice: SQLite

**Why SQLite**

- **Zero setup** — no database server to install; a single `app.db` file in the project root.
- **Portable** — easy for reviewers to clone, migrate, seed, and run.
- **Sufficient for scope** — single-user internal tool with modest data volume; supports FKs, indexes, transactions, and enums.

**Swapping to Postgres**

Set `DATABASE_URL` in `.env`:

```
DATABASE_URL=postgresql+psycopg2://user:pass@localhost/ticketdb
```

Run the same Alembic migrations. See [data-model.md](../data-model.md) for Postgres-specific notes (timestamps, optional native ENUM types, search indexes).

---

## Schema

Three tables: `users`, `tickets`, `comments`. Full definitions in [data-model.md](../data-model.md).

| Table | ORM model | Key points |
|-------|-----------|------------|
| `users` | `User` | id, name, email (unique), role enum |
| `tickets` | `Ticket` | FKs to users; priority/status enums; server-managed timestamps |
| `comments` | `Comment` | FK to ticket + author; append-only |

Migrations live in `database/migrations/versions/`.

---

## Run migrations

From the project root with venv activated:

```bash
# Apply all pending migrations
alembic upgrade head

# Check current revision
alembic current

# Generate a new migration after model changes (development only)
alembic revision --autogenerate -m "describe change"
```

Initial migration: `database/migrations/versions/001_initial_schema.py` — creates all tables and indexes.

Default database URL: `sqlite:///./app.db` (from `.env` or `config.py` default).

---

## Seed data

Idempotent seed script — safe to run multiple times; skips if users already exist.

```bash
python -m src.backend.seed
```

**Inserts:**

- **4 users** — Admin, Agent, Manager, Requester (distinct roles)
- **12 tickets** — spread across every status (Open, In Progress, Resolved, Closed, Cancelled) and priority (Low, Medium, High)
- **8 comments** — on various tickets

> **Note:** Seed sets ticket statuses directly for demo coverage. At runtime, all status changes must go through the state machine service (`POST /api/tickets/{id}/status`).

**Verify seed:**

```bash
# Count rows via API (server must be running)
curl http://localhost:8000/api/users
curl http://localhost:8000/api/tickets

# Or inspect SQLite directly
sqlite3 app.db "SELECT COUNT(*) FROM users;"
sqlite3 app.db "SELECT COUNT(*) FROM tickets;"
sqlite3 app.db "SELECT COUNT(*) FROM comments;"
sqlite3 app.db "SELECT status, COUNT(*) FROM tickets GROUP BY status;"
```

Expected counts: 4 users, 12 tickets, 8 comments.

---

## Reset database

To start fresh (destroys all data):

```bash
# Stop the running server first
rm -f app.db
alembic upgrade head
python -m src.backend.seed
```

For tests, pytest uses an in-memory SQLite database (`tests/conftest.py`) — no `app.db` file is touched.

---

## File locations

| Path | Purpose |
|------|---------|
| `src/backend/app/models/entities.py` | SQLAlchemy ORM models |
| `src/backend/app/database.py` | Engine, session, `get_db` dependency |
| `src/backend/seed.py` | Idempotent seed script |
| `database/migrations/` | Alembic migration scripts |
| `alembic.ini` | Alembic config (script location, logging) |
| `app.db` | SQLite database file (gitignored) |
