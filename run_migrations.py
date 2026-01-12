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

            # Check if style_option column exists
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='user_onboarding'
                AND column_name='style_option'
            """))

            column_exists = result.fetchone() is not None

            if not column_exists:
                print("  ➕ Adding style_option column to user_onboarding table...")
                conn.execute(text("""
                    ALTER TABLE user_onboarding
                    ADD COLUMN style_option VARCHAR
                """))
                conn.commit()
                print("  ✅ Column style_option added successfully!")
            else:
                print("  ✅ Column style_option already exists")

            # Check if creator_url column exists
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='user_onboarding'
                AND column_name='creator_url'
            """))

            column_exists = result.fetchone() is not None

            if not column_exists:
                print("  ➕ Adding creator_url column to user_onboarding table...")
                conn.execute(text("""
                    ALTER TABLE user_onboarding
                    ADD COLUMN creator_url VARCHAR
                """))
                conn.commit()
                print("  ✅ Column creator_url added successfully!")
            else:
                print("  ✅ Column creator_url already exists")

            # Check if fallback_style column exists
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='user_onboarding'
                AND column_name='fallback_style'
            """))

            column_exists = result.fetchone() is not None

            if not column_exists:
                print("  ➕ Adding fallback_style column to user_onboarding table...")
                conn.execute(text("""
                    ALTER TABLE user_onboarding
                    ADD COLUMN fallback_style VARCHAR
                """))
                conn.commit()
                print("  ✅ Column fallback_style added successfully!")
            else:
                print("  ✅ Column fallback_style already exists")

        print("✅ Migrations completed successfully!")

    except Exception as e:
        print(f"❌ Error running migrations: {e}")
        # Don't fail the app startup, just log the error
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_migrations()
