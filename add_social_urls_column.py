"""
Migration script to add social_urls column to user_onboarding table
Run this script once to update existing database
"""
import os
from sqlalchemy import create_engine, text

# Get database URL from environment or use default
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

# Create engine
engine = create_engine(DATABASE_URL)

def add_social_urls_column():
    """Add social_urls column to user_onboarding table if it doesn't exist"""
    with engine.connect() as conn:
        # Check if column exists
        result = conn.execute(text("""
            SELECT COUNT(*)
            FROM pragma_table_info('user_onboarding')
            WHERE name='social_urls'
        """))

        column_exists = result.scalar() > 0

        if not column_exists:
            print("Adding social_urls column to user_onboarding table...")
            conn.execute(text("""
                ALTER TABLE user_onboarding
                ADD COLUMN social_urls TEXT
            """))
            conn.commit()
            print("✓ Column added successfully!")
        else:
            print("✓ Column social_urls already exists")

if __name__ == "__main__":
    print("Starting migration...")
    add_social_urls_column()
    print("Migration completed!")
