-- 009_create_conversation_tables.sql
-- Future-ready minimal conversation storage. No exposure API in Phase 2.
--
-- PRIVACY POLICY (Phase 2): never store passwords, OTPs, PINs, bank
-- credentials, API keys, authentication secrets, or unnecessary personally
-- identifying information (citizenship numbers, full addresses, phone
-- numbers) in these tables. Conversations may be sensitive; keep them minimal.

CREATE TABLE IF NOT EXISTS conversation_sessions (
    id         UUID PRIMARY KEY,
    session_id UUID UNIQUE NOT NULL,
    status     VARCHAR(32) NOT NULL,
    language   VARCHAR(32),
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at   TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS conversation_messages (
    id         UUID PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES conversation_sessions(id) ON DELETE CASCADE,
    role       VARCHAR(16) NOT NULL,
    input_mode VARCHAR(16),
    content    TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT conversation_messages_role_check CHECK (role IN ('user', 'assistant', 'system')),
    CONSTRAINT conversation_messages_input_mode_check CHECK (input_mode IN ('voice', 'text'))
);

CREATE INDEX IF NOT EXISTS idx_conversation_messages_session_id ON conversation_messages (session_id);

COMMENT ON TABLE conversation_sessions IS
    'One row per future conversation. Privacy: no credentials or unnecessary PII.';
COMMENT ON TABLE conversation_messages IS
    'Future conversation history. Privacy: never persist OTPs, passwords, PINs, '
    'bank credentials, API keys, or unnecessary personally identifying information.';