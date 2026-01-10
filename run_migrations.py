"""
Run database migrations
This script should be executed before starting the FastAPI application
"""
import os
from sqlalchemy import create_engine, text

def run_migrations():
    """Execute all pending migrations"""
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("⚠️  DATABASE_URL not set, skipping migrations")
        return

    print("🔄 Running database migrations...")

    try:
        engine = create_engine(database_url)

        with engine.connect() as conn:
            # Check if social_urls column exists
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='user_onboarding'
                AND column_name='social_urls'
            """))

            column_exists = result.fetchone() is not None

            if not column_exists:
                print("  ➕ Adding social_urls column to user_onboarding table...")
                conn.execute(text("""
                    ALTER TABLE user_onboarding
                    ADD COLUMN social_urls TEXT
                """))
                conn.commit()
                print("  ✅ Column social_urls added successfully!")
            else:
                print("  ✅ Column social_urls already exists")

        print("✅ Migrations completed successfully!")

    except Exception as e:
        print(f"❌ Error running migrations: {e}")
        # Don't fail the app startup, just log the error
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_migrations()
