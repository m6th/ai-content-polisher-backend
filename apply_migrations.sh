#!/bin/bash
# Script to apply database migrations

echo "Applying database migrations..."
alembic upgrade head

if [ $? -eq 0 ]; then
    echo "✅ Migrations applied successfully!"
else
    echo "❌ Error applying migrations"
    exit 1
fi
