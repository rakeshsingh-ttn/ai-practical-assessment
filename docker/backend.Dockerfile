FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libsqlite3-0 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid appuser --create-home appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY alembic.ini .
COPY database/ database/
COPY src/ src/
COPY docker/backend-entrypoint.sh /app/docker/backend-entrypoint.sh

RUN chmod +x /app/docker/backend-entrypoint.sh \
    && mkdir -p /data \
    && chown -R appuser:appuser /app /data

VOLUME /data

USER appuser

ENV DATABASE_URL=sqlite:////data/app.db

EXPOSE 8000

ENTRYPOINT ["/app/docker/backend-entrypoint.sh"]
