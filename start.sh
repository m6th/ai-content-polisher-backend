#!/bin/bash
set -e

echo "🔄 Checking database migrations..."

# Get current migration version
CURRENT=$(alembic current 2>/dev/null | grep -oP '(?<=^)[a-z0-9]+' | head -1)

if [ -z "$CURRENT" ] || [ "$CURRENT" == "None" ]; then
    echo "⚠️  No migration version found in alembic_version table"
    echo "🔍 Detecting actual database state..."

    # Check if scheduled_contents table exists (migration g3h4i5j6k7l8)
    TABLE_EXISTS=$(python3 -c "
import os
from sqlalchemy import create_engine, inspect
engine = create_engine(os.getenv('DATABASE_URL'))
inspector = inspect(engine)
tables = inspector.get_table_names()
print('scheduled_contents' in tables)
" 2>/dev/null || echo "false")

    if [ "$TABLE_EXISTS" == "True" ]; then
        echo "✓ Found scheduled_contents table, stamping to g3h4i5j6k7l8..."
        alembic stamp g3h4i5j6k7l8
    else
        echo "⚠️  scheduled_contents not found, stamping to d8cbae94787a..."
        alembic stamp d8cbae94787a
    fi

    echo "🔄 Applying remaining migrations..."
    alembic upgrade head
elif [ "$CURRENT" == "d8cbae94787a" ]; then
    echo "✓ Database is at version d8cbae94787a"
    echo "🔄 Applying new migrations..."
    alembic upgrade head
else
    echo "ℹ️  Current version: $CURRENT"
    echo "🔄 Applying pending migrations..."
    alembic upgrade head
fi

echo "🚀 Starting application..."
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
