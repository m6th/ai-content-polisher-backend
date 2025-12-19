#!/bin/bash
set -e

echo "🔄 Applying database migrations..."
alembic upgrade head

echo "🚀 Starting application..."
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
