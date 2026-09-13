#!/bin/bash
# Run Alembic migrations, then start the server.
# Railway sets $PORT dynamically.
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting Carbon Core API..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
