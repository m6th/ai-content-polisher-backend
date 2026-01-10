-- Migration: Add social_urls column to user_onboarding table
-- Date: 2026-01-10

-- Add the social_urls column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name='user_onboarding'
        AND column_name='social_urls'
    ) THEN
        ALTER TABLE user_onboarding ADD COLUMN social_urls TEXT;
        RAISE NOTICE 'Column social_urls added successfully';
    ELSE
        RAISE NOTICE 'Column social_urls already exists';
    END IF;
END $$;
