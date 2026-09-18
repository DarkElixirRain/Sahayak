-- 003_create_legal_documents.sql
-- Laws, regulations, codes, rules, directives, procedures, policies...

CREATE TABLE IF NOT EXISTS legal_documents (
    id                 UUID PRIMARY KEY,
    domain_id          UUID REFERENCES legal_domains(id) ON DELETE SET NULL,
    title              VARCHAR(255) NOT NULL,
    short_title        VARCHAR(255),
    document_type      VARCHAR(64) NOT NULL,
    jurisdiction       VARCHAR(128),
    issuing_authority  VARCHAR(255),
    official_source_url TEXT,
    language           VARCHAR(32),
    effective_date     DATE,
    status             VARCHAR(64),
    description        TEXT,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT legal_documents_document_type_check CHECK (
        document_type IN (
            'act', 'code', 'regulation', 'rule', 'directive',
            'procedure', 'policy', 'other'
        )
    )
);

CREATE INDEX IF NOT EXISTS idx_legal_documents_domain_id ON legal_documents (domain_id);
CREATE INDEX IF NOT EXISTS idx_legal_documents_title ON legal_documents (title);

-- Deterministic import/re-import matching key.
CREATE UNIQUE INDEX IF NOT EXISTS uq_legal_documents_domain_title_type
    ON legal_documents (domain_id, title, document_type)
    WHERE domain_id IS NOT NULL;

COMMENT ON TABLE legal_documents IS
    'Laws and regulations represented as documents. One document may map to many provisions.';