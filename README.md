# Support Ticket Management System

Internal support ticket app — FastAPI backend, React (Vite) frontend, SQLite database.

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

- App: http://localhost:5173

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

## Project layout

```
src/backend/app/
  main.py           # App factory, CORS, router registration
  config.py         # pydantic-settings (.env)
  database.py       # SQLAlchemy engine + get_db dependency
  routers/          # HTTP endpoints
  services/         # Business logic
  models/           # SQLAlchemy ORM entities
  schemas/          # Pydantic request/response models
```
