-- Add creator_posts column to user_onboarding table
ALTER TABLE user_onboarding ADD COLUMN IF NOT EXISTS creator_posts TEXT;
