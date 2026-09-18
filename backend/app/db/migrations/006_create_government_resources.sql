-- 006_create_government_resources.sql
-- Practical government/legal service information ("where do I file a complaint?"),
-- kept separate from statutory provisions.
-- required_documents and contact_information are free-form JSONB payloads.

CREATE TABLE IF NOT EXISTS government_resources (
    id                  UUID PRIMARY KEY,
    domain_id           UUID REFERENCES legal_domains(id) ON DELETE SET NULL,
    title               VARCHAR(255) NOT NULL,
    description         TEXT,
    authority_name      VARCHAR(255),
    service_name        VARCHAR(255),
    instructions        TEXT,
    required_documents  JSONB,
    contact_information JSONB,
    official_url        TEXT,
    source_id           UUID REFERENCES sources(id) ON DELETE SET NULL,
    is_verified         BOOLEAN NOT NULL DEFAULT FALSE,
    verified_at         TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_government_resources_domain_id ON government_resources (domain_id);
CREATE INDEX IF NOT EXISTS idx_government_resources_verified ON government_resources (is_verified);

COMMENT ON TABLE government_resources IS
    'Practical government/legal service information, distinct from legal provisions. '
    'No sensitive personal data should ever be stored here.';