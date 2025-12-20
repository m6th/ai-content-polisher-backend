#!/bin/bash
set -e

echo "🔄 Checking database migrations..."

# Get current migration version
CURRENT=$(alembic current 2>/dev/null | grep -oP '(?<=^)[a-z0-9]+' | head -1)

if [ "$CURRENT" == "d8cbae94787a" ]; then
    echo "✓ Database is at expected version (d8cbae94787a)"
    echo "🔄 Applying new migrations only..."
    alembic upgrade head
elif [ -z "$CURRENT" ] || [ "$CURRENT" == "None" ]; then
    echo "⚠️  No migration version found, stamping to d8cbae94787a..."
    alembic stamp d8cbae94787a
    echo "🔄 Applying remaining migrations..."
    alembic upgrade head
else
    echo "ℹ️  Current version: $CURRENT"
    echo "🔄 Applying all pending migrations..."
    alembic upgrade head
fi

echo "🚀 Starting application..."
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
