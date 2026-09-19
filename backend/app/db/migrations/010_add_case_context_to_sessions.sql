-- 010_add_case_context_to_sessions.sql
-- Persist structured case context as JSONB in conversation_sessions.
--
-- CaseContext was previously held only in a process-level dict (CaseContextManager),
-- meaning it was lost on process restart and incompatible with multi-worker
-- deployments. Persisting it here makes context durable and process-independent.
--
-- The column is nullable: existing sessions without any accumulated context will
-- have NULL, which is equivalent to an empty CaseContext.
--
-- The schema intentionally avoids a separate normalized table: case context is
-- a flexible, evolving set of optional fields, and JSONB lets us add/remove
-- fields without further migrations.

ALTER TABLE conversation_sessions
    ADD COLUMN IF NOT EXISTS case_context JSONB;

COMMENT ON COLUMN conversation_sessions.case_context IS
    'Structured case information accumulated over the conversation. '
    'Stored as JSONB for flexibility. Never contains passwords, PINs, '
    'financial credentials, or other sensitive PII beyond what the user '
    'voluntarily provides for legal intake.';
