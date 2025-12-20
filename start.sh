#!/bin/bash
set -e

echo "🔄 Checking database migrations..."

# Get current migration version
CURRENT=$(alembic current 2>/dev/null | grep -oP '(?<=^)[a-z0-9]+' | head -1 || echo "")

if [ -z "$CURRENT" ]; then
    echo "⚠️  No migration version found in alembic_version table"
    echo "🔍 Detecting actual database state by checking existing tables..."

    # Check if teams table exists (last migration h4i5j6k7l8m9)
    TEAMS_EXISTS=$(python3 << 'PYEOF'
import os
import sys
try:
    from sqlalchemy import create_engine, text
    engine = create_engine(os.getenv('DATABASE_URL'))
    with engine.connect() as conn:
        result = conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'teams')"))
        exists = result.scalar()
        print('true' if exists else 'false')
except Exception as e:
    print('false', file=sys.stderr)
    print('false')
PYEOF
)

    # Check if scheduled_contents table exists (migration g3h4i5j6k7l8)
    SCHEDULED_EXISTS=$(python3 << 'PYEOF'
import os
import sys
try:
    from sqlalchemy import create_engine, text
    engine = create_engine(os.getenv('DATABASE_URL'))
    with engine.connect() as conn:
        result = conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'scheduled_contents')"))
        exists = result.scalar()
        print('true' if exists else 'false')
except Exception as e:
    print('false', file=sys.stderr)
    print('false')
PYEOF
)

    if [ "$TEAMS_EXISTS" == "true" ]; then
        echo "✓ Found teams table - database appears fully migrated, stamping to head..."
        alembic stamp head
    elif [ "$SCHEDULED_EXISTS" == "true" ]; then
        echo "✓ Found scheduled_contents table, stamping to g3h4i5j6k7l8..."
        alembic stamp g3h4i5j6k7l8
        echo "🔄 Applying remaining migrations..."
        alembic upgrade head
    else
        echo "⚠️  Tables not found, stamping to d8cbae94787a..."
        alembic stamp d8cbae94787a
        echo "🔄 Applying all new migrations..."
        alembic upgrade head
    fi
elif [ "$CURRENT" == "d8cbae94787a" ]; then
    echo "✓ Database is at version d8cbae94787a"
    echo "🔄 Applying new migrations..."
    alembic upgrade head
else
    echo "ℹ️  Current version: $CURRENT"
    echo "🔄 Applying pending migrations..."
    alembic upgrade head
fi

echo "✅ Migrations complete!"
echo "🚀 Starting application..."
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
