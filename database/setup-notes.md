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

Docker: reset the named volume if a previous failed seed left a bad schema or partial data:

```bash
docker compose down -v && docker compose up --build
```

---

## Enum columns & CHECK constraints (migration 002)

### Symptom

After `alembic upgrade head`, seeding failed with:

```
IntegrityError: CHECK constraint failed: ck_users_role
INSERT INTO users ... ('Alice Admin', 'alice@example.com', 'ADMIN')
```

The CHECK constraint allows display values (`Admin`, `Agent`, …). The insert used `ADMIN` (enum **member name**).

### How we traced it

| Step | Action | Result |
|------|--------|--------|
| 1 | Read the error | `ck_users_role` rejected the stored value |
| 2 | Inspect SQL parameters | Value was `'ADMIN'`, not `'Admin'` |
| 3 | Reproduce locally | `alembic upgrade head` + `python -m src.backend.seed` failed |
| 4 | Bisect migrations | After **001 only** → seed succeeded; after **001 + 002** → seed failed |

Migration `002_check_constraints.py` was the trigger, not the seed script or enum definitions themselves.

### Root cause

Three things interacted:

1. **API contract** — enums use display **values** (`Admin`), not Python member names (`ADMIN`). See `UserRole`, `TicketPriority`, and `TicketStatus` in `entities.py`.
2. **Migration 001** — creates columns with `sa.Enum("Admin", "Agent", …)`, which binds correctly on a fresh schema.
3. **Migration 002** — adds CHECK constraints via `op.batch_alter_table`. On SQLite this **recreates the table**; enum columns become plain `VARCHAR` without the original `sa.Enum` metadata. SQLAlchemy then persisted member **names** (`ADMIN`) while CHECK constraints still required **values** (`Admin`).

The CHECK constraints were correct. Enum binding broke after the batch table rebuild.

### Why pytest did not catch it

| Path | CHECK constraints? | Enum binding | Outcome |
|------|-------------------|--------------|---------|
| pytest (`Base.metadata.create_all`) | No | ORM model directly | Tests passed |
| `alembic upgrade 001` + seed | No | Migration `sa.Enum` | Seed worked |
| `alembic upgrade head` (Docker / prod-like) | Yes | Broken after batch recreate | Seed failed |

Tests and `create_all()` never exercised the real migrate → seed startup path.

### Fix

Enum columns in `entities.py` use a shared `_enum_column()` helper that always persists `.value`:

```python
def _enum_column(enum_class):
    return Enum(
        enum_class,
        native_enum=False,
        values_callable=lambda members: [member.value for member in members],
    )
```

Applied to `role`, `priority`, and `status`. This keeps storage aligned with CHECK constraints and API JSON even if a future migration recreates columns as plain strings.

### Learnings

- **SQLite `batch_alter_table` is a table rewrite** — type metadata (enums, defaults) can change silently; treat batch migrations as full schema changes, not small constraint adds.
- **Enum name vs value** — always know which representation CHECK constraints, API responses, and seed data use (here: **value**).
- **Migrate + seed is a separate test path** — green `pytest` does not prove Docker or `alembic upgrade head` + seed works; verify that path explicitly.
- **Bisect migrations early** — `alembic upgrade 001` vs `upgrade head` quickly isolates migration side effects.

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
