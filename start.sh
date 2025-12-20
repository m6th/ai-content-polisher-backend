#!/bin/bash
set -e

echo "🔄 Checking database migrations..."

# Get current migration version
CURRENT=$(alembic current 2>/dev/null | grep -oP '(?<=^)[a-z0-9]+' | head -1 || echo "")

if [ "$CURRENT" == "d8cbae94787a" ]; then
    echo "✓ Database is at version d8cbae94787a"
    echo "🔍 Checking if format_name column exists..."

    # Check if format_name column exists in generated_contents (migration f2b3c4d5e6f7)
    FORMAT_NAME_EXISTS=$(python3 << 'PYEOF'
import os
import sys
try:
    from sqlalchemy import create_engine, text
    engine = create_engine(os.getenv('DATABASE_URL'))
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_name = 'generated_contents'
                AND column_name = 'format_name'
            )
        """))
        exists = result.scalar()
        print('true' if exists else 'false')
except Exception as e:
    print('false', file=sys.stderr)
    print('false')
PYEOF
)

    if [ "$FORMAT_NAME_EXISTS" == "true" ]; then
        echo "✓ format_name column exists, checking for newer tables..."

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

        if [ "$SCHEDULED_EXISTS" == "true" ]; then
            echo "⚠️  Found scheduled_contents table but alembic thinks we're at d8cbae94787a"
            echo "🔧 Fixing alembic_version to match actual database state..."

            # Check if teams table also exists
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

            if [ "$TEAMS_EXISTS" == "true" ]; then
                echo "✓ Found teams table, but need to check format_name column first..."

                # Check if format_name column exists
                FORMAT_COL_EXISTS=$(python3 << 'PYEOF'
import os
import sys
try:
    from sqlalchemy import create_engine, text
    engine = create_engine(os.getenv('DATABASE_URL'))
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_name = 'generated_contents'
                AND column_name = 'format_name'
            )
        """))
        exists = result.scalar()
        print('true' if exists else 'false')
except Exception as e:
    print('false', file=sys.stderr)
    print('false')
PYEOF
)

                if [ "$FORMAT_COL_EXISTS" == "true" ]; then
                    echo "✓ format_name column exists, stamping to head (h4i5j6k7l8m9)..."
                    alembic stamp head
                else
                    echo "⚠️  format_name column missing, adding it manually..."
                    python3 << 'PYEOF'
import os
from sqlalchemy import create_engine, text
engine = create_engine(os.getenv('DATABASE_URL'))
with engine.connect() as conn:
    conn.execute(text("ALTER TABLE generated_contents ADD COLUMN IF NOT EXISTS format_name VARCHAR"))
    conn.commit()
print("✓ Added format_name column")
PYEOF
                    echo "✓ Stamping to head (h4i5j6k7l8m9)..."
                    alembic stamp head
                fi
            else
                echo "✓ Stamping to g3h4i5j6k7l8 (scheduled_contents exists)..."
                alembic stamp g3h4i5j6k7l8
                echo "🔄 Applying teams migration..."
                alembic upgrade head
            fi
        else
            echo "✓ Stamping to f2b3c4d5e6f7 (format_name exists)..."
            alembic stamp f2b3c4d5e6f7
            echo "🔄 Applying remaining migrations..."
            alembic upgrade head
        fi
    else
        echo "⚠️  format_name column missing, applying all new migrations..."
        alembic upgrade head
    fi
elif [ -z "$CURRENT" ]; then
    echo "⚠️  No migration version found in alembic_version table"
    echo "🔧 Stamping to d8cbae94787a as baseline..."
    alembic stamp d8cbae94787a
    echo "🔄 Re-running migration check..."
    exec "$0"
else
    echo "ℹ️  Current version: $CURRENT"
    echo "🔄 Applying pending migrations..."
    alembic upgrade head
fi

echo "✅ Migrations complete!"
echo "🚀 Starting application..."
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
