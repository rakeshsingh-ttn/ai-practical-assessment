#!/bin/sh
set -e

cd /app

alembic upgrade head
python -m src.backend.seed

exec uvicorn src.backend.app.main:app --host 0.0.0.0 --port 8000
