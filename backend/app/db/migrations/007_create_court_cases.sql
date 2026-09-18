-- 007_create_court_cases.sql
-- Metadata + structured summaries of VERIFIED official court decisions only.
-- Do NOT import fabricated cases or generated "conclusions" labeled as rulings.

CREATE TABLE IF NOT EXISTS court_cases (
    id              UUID PRIMARY KEY,
    domain_id       UUID REFERENCES legal_domains(id) ON DELETE SET NULL,
    court_name      VARCHAR(255) NOT NULL,
    case_number     VARCHAR(128),
    decision_date   DATE,
    title           VARCHAR(512),
    case_type       VARCHAR(64),
    facts_summary   TEXT,
    legal_issues    TEXT,
    decision_summary TEXT,
    official_url    TEXT,
    source_id       UUID REFERENCES sources(id) ON DELETE SET NULL,
    is_verified     BOOLEAN NOT NULL DEFAULT FALSE,
    verified_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_court_cases_domain_id ON court_cases (domain_id);
CREATE INDEX IF NOT EXISTS idx_court_cases_decision_date ON court_cases (decision_date);
CREATE INDEX IF NOT EXISTS idx_court_cases_verified ON court_cases (is_verified);

COMMENT ON TABLE court_cases IS
    'Verified official court decisions only. No fabricated cases or case numbers.';
COMMENT ON COLUMN court_cases.is_verified IS
    'FALSE by default; set TRUE only after manual verification against the official record.';