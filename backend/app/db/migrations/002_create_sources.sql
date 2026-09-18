-- 002_create_sources.sql
-- Provenance: where every legal fact came from. Created before documents
-- and knowledge chunks so those tables can reference it.

CREATE TABLE IF NOT EXISTS sources (
    id           UUID PRIMARY KEY,
    name         VARCHAR(255) NOT NULL,
    source_type  VARCHAR(64) NOT NULL,
    organization VARCHAR(255),
    official_url TEXT,
    description  TEXT,
    is_official  BOOLEAN NOT NULL DEFAULT FALSE,
    is_verified  BOOLEAN NOT NULL DEFAULT FALSE,
    verified_at  TIMESTAMPTZ,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT sources_source_type_check CHECK (
        source_type IN (
            'government', 'law_commission', 'court', 'ministry',
            'police', 'regulator', 'official_document', 'other'
        )
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_sources_official_url
    ON sources (official_url) WHERE official_url IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_sources_name ON sources (name);

COMMENT ON TABLE sources IS
    'Official origin of legal knowledge. The LLM is never the source of truth; '
    'every verified knowledge record must trace back to a source row here.';
COMMENT ON COLUMN sources.is_verified IS
    'True only when the source itself has been checked against the original official material.';