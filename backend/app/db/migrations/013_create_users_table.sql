-- 013_create_users_table.sql
-- Create users table for authentication and associate with conversation_sessions

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- For MVP, we will allow user_id to be nullable so existing sessions don't break migration.
-- But API endpoints will enforce ownership going forward.
ALTER TABLE conversation_sessions ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_conversation_sessions_user_id ON conversation_sessions (user_id);

COMMENT ON TABLE users IS 'User authentication records. Passwords are securely hashed.';
