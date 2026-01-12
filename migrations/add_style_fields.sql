-- Migration: Add style_option, creator_url, and fallback_style columns to user_onboarding table
-- Date: 2026-01-12

-- Add the style_option column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name='user_onboarding'
        AND column_name='style_option'
    ) THEN
        ALTER TABLE user_onboarding ADD COLUMN style_option VARCHAR;
        RAISE NOTICE 'Column style_option added successfully';
    ELSE
        RAISE NOTICE 'Column style_option already exists';
    END IF;
END $$;

-- Add the creator_url column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name='user_onboarding'
        AND column_name='creator_url'
    ) THEN
        ALTER TABLE user_onboarding ADD COLUMN creator_url VARCHAR;
        RAISE NOTICE 'Column creator_url added successfully';
    ELSE
        RAISE NOTICE 'Column creator_url already exists';
    END IF;
END $$;

-- Add the fallback_style column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name='user_onboarding'
        AND column_name='fallback_style'
    ) THEN
        ALTER TABLE user_onboarding ADD COLUMN fallback_style VARCHAR;
        RAISE NOTICE 'Column fallback_style added successfully';
    ELSE
        RAISE NOTICE 'Column fallback_style already exists';
    END IF;
END $$;
