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
