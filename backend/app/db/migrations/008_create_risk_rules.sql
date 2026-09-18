-- 008_create_risk_rules.sql
-- Deterministic safety/scam detection rules, independent of the LLM.
-- patterns is a free-form JSONB array of trigger words/phrases.
-- The matching engine itself is implemented in a later phase.

CREATE TABLE IF NOT EXISTS risk_rules (
    id          UUID PRIMARY KEY,
    domain_id   UUID REFERENCES legal_domains(id) ON DELETE SET NULL,
    key         VARCHAR(64) UNIQUE NOT NULL,
    label       VARCHAR(255) NOT NULL,
    description TEXT,
    patterns    JSONB NOT NULL,
    severity    VARCHAR(32) NOT NULL,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT risk_rules_severity_check CHECK (
        severity IN ('low', 'medium', 'high', 'critical')
    )
);

CREATE INDEX IF NOT EXISTS idx_risk_rules_domain_id ON risk_rules (domain_id);
CREATE INDEX IF NOT EXISTS idx_risk_rules_is_active ON risk_rules (is_active);

COMMENT ON TABLE risk_rules IS
    'Deterministic risk/scam detection data. Risk detection is a SEPARATE system from '
    'general legal knowledge — not every legal question is a safety risk.';