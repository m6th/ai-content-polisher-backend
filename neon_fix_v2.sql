-- Script de correction v2 pour Neon
-- Exécuter dans Neon SQL Editor

-- 1. Supprimer TOUTES les tables d'abord (ordre important à cause des foreign keys)
DROP TABLE IF EXISTS user_style_profiles CASCADE;
DROP TABLE IF EXISTS user_onboarding CASCADE;
DROP TABLE IF EXISTS api_keys CASCADE;
DROP TABLE IF EXISTS team_invitations CASCADE;
DROP TABLE IF EXISTS team_members CASCADE;
DROP TABLE IF EXISTS teams CASCADE;
DROP TABLE IF EXISTS scheduled_contents CASCADE;
DROP TABLE IF EXISTS usage_analytics CASCADE;
DROP TABLE IF EXISTS generated_contents CASCADE;
DROP TABLE IF EXISTS content_requests CASCADE;
DROP TABLE IF EXISTS content_history CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS alembic_version CASCADE;

-- 2. Supprimer les types ENUM existants
DROP TYPE IF EXISTS subscriptiontier CASCADE;
DROP TYPE IF EXISTS platform CASCADE;

-- 3. Créer les types ENUM
CREATE TYPE subscriptiontier AS ENUM ('free', 'basic', 'pro', 'enterprise');
CREATE TYPE platform AS ENUM ('linkedin', 'instagram', 'tiktok', 'facebook', 'twitter', 'multi_format');

-- 4. Créer la table users
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    password_hash VARCHAR,
    google_id VARCHAR UNIQUE,
    name VARCHAR,
    created_at TIMESTAMP DEFAULT NOW(),
    subscription_tier subscriptiontier DEFAULT 'free',
    current_plan VARCHAR DEFAULT 'free',
    plan_started_at TIMESTAMP DEFAULT NOW(),
    credits_remaining INTEGER DEFAULT 10,
    last_credit_renewal TIMESTAMP DEFAULT NOW(),
    email_verified INTEGER DEFAULT 0,
    verification_code VARCHAR,
    verification_code_expires TIMESTAMP,
    is_admin INTEGER DEFAULT 0,
    stripe_customer_id VARCHAR UNIQUE,
    stripe_subscription_id VARCHAR,
    subscription_status VARCHAR DEFAULT 'inactive',
    subscription_end_date TIMESTAMP,
    has_used_pro_trial BOOLEAN DEFAULT FALSE NOT NULL,
    pro_trial_activated_at TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_google_id ON users(google_id);

-- 5. Créer content_requests
CREATE TABLE content_requests (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    original_text TEXT NOT NULL,
    platform VARCHAR NOT NULL,
    tone VARCHAR,
    language VARCHAR DEFAULT 'fr',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_content_requests_user_id ON content_requests(user_id);

-- 6. Créer generated_contents
CREATE TABLE generated_contents (
    id SERIAL PRIMARY KEY,
    request_id INTEGER REFERENCES content_requests(id) NOT NULL,
    polished_text TEXT NOT NULL,
    format_name VARCHAR,
    variant_number INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_generated_contents_request_id ON generated_contents(request_id);

-- 7. Créer usage_analytics
CREATE TABLE usage_analytics (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    tokens_used INTEGER,
    request_date TIMESTAMP DEFAULT NOW(),
    platform platform
);

CREATE INDEX idx_usage_analytics_user_id ON usage_analytics(user_id);

-- 8. Créer scheduled_contents
CREATE TABLE scheduled_contents (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    content_request_id INTEGER REFERENCES content_requests(id),
    generated_content_id INTEGER REFERENCES generated_contents(id),
    scheduled_date TIMESTAMP NOT NULL,
    platform VARCHAR NOT NULL,
    status VARCHAR DEFAULT 'scheduled',
    title VARCHAR,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    reminder_24h_sent BOOLEAN DEFAULT FALSE NOT NULL,
    reminder_1h_sent BOOLEAN DEFAULT FALSE NOT NULL,
    reminder_24h_sent_at TIMESTAMP,
    reminder_1h_sent_at TIMESTAMP
);

CREATE INDEX idx_scheduled_contents_user_id ON scheduled_contents(user_id);

-- 9. Créer teams
CREATE TABLE teams (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    owner_id INTEGER REFERENCES users(id) NOT NULL,
    plan VARCHAR NOT NULL,
    max_members INTEGER DEFAULT 2,
    team_credits INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 10. Créer team_members
CREATE TABLE team_members (
    id SERIAL PRIMARY KEY,
    team_id INTEGER REFERENCES teams(id) NOT NULL,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    role VARCHAR DEFAULT 'member',
    status VARCHAR DEFAULT 'active',
    joined_at TIMESTAMP DEFAULT NOW()
);

-- 11. Créer team_invitations
CREATE TABLE team_invitations (
    id SERIAL PRIMARY KEY,
    team_id INTEGER REFERENCES teams(id) NOT NULL,
    email VARCHAR NOT NULL,
    invited_by INTEGER REFERENCES users(id) NOT NULL,
    token VARCHAR UNIQUE NOT NULL,
    status VARCHAR DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL
);

-- 12. Créer api_keys
CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    name VARCHAR(100) NOT NULL,
    key_prefix VARCHAR(20) UNIQUE NOT NULL,
    key_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    last_used_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE NOT NULL
);

CREATE INDEX idx_api_keys_key_prefix ON api_keys(key_prefix);
CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);

-- 13. Créer user_onboarding
CREATE TABLE user_onboarding (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    completed BOOLEAN DEFAULT FALSE NOT NULL,
    discovery_source VARCHAR,
    preferred_networks TEXT,
    social_urls TEXT,
    style_option VARCHAR,
    creator_url VARCHAR,
    preferred_style VARCHAR,
    fallback_style VARCHAR,
    consent_data_storage BOOLEAN DEFAULT FALSE NOT NULL,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_user_onboarding_user_id ON user_onboarding(user_id);

-- 14. Créer user_style_profiles
CREATE TABLE user_style_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    style_name VARCHAR NOT NULL,
    style_type VARCHAR NOT NULL,
    platform VARCHAR,
    source_url VARCHAR NOT NULL,
    style_analysis TEXT,
    sample_posts TEXT,
    status VARCHAR DEFAULT 'pending' NOT NULL,
    error_message TEXT,
    last_analyzed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_user_style_profiles_user_id ON user_style_profiles(user_id);

-- Vérification
SELECT 'Toutes les tables ont été créées avec succès!' as status;
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;
