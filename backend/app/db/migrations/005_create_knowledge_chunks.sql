-- 005_create_knowledge_chunks.sql
-- Retrieval-ready pieces of legal knowledge.
--
-- IMPORTANT: No embeddings, no vector columns, no pgvector in Phase 2.
-- This table is pre-structured so Phase 3/4 can add semantic retrieval on top.

CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id           UUID PRIMARY KEY,
    document_id  UUID NOT NULL REFERENCES legal_documents(id) ON DELETE CASCADE,
    provision_id UUID REFERENCES legal_provisions(id) ON DELETE SET NULL,
    domain_id    UUID REFERENCES legal_domains(id) ON DELETE SET NULL,
    source_id    UUID REFERENCES sources(id) ON DELETE SET NULL,
    title        VARCHAR(512),
    content      TEXT NOT NULL,
    language     VARCHAR(32),
    chunk_index  INTEGER,
    source_type  VARCHAR(64),
    is_verified  BOOLEAN NOT NULL DEFAULT FALSE,
    verified_at  TIMESTAMPTZ,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_document_id ON knowledge_chunks (document_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_provision_id ON knowledge_chunks (provision_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_domain_id ON knowledge_chunks (domain_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_is_verified ON knowledge_chunks (is_verified);
CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_language ON knowledge_chunks (language);

-- Re-import safety: the same (document, provision, chunk index, language)
-- combination cannot exist twice.
CREATE UNIQUE INDEX IF NOT EXISTS uq_knowledge_chunks_doc_prov_idx_lang
    ON knowledge_chunks (
        document_id,
        COALESCE(provision_id, '00000000-0000-0000-0000-000000000000'::uuid),
        chunk_index,
        COALESCE(language, '')
    );

COMMENT ON TABLE knowledge_chunks IS
    'Retrieval-ready legal knowledge. Verification state is explicit: never present a '
    'record as verified unless is_verified = TRUE AND its source is verified. '
    'No vector columns are present in Phase 2; this table is ready for future embeddings.';
COMMENT ON COLUMN knowledge_chunks.is_verified IS
    'TRUE only when the content has been checked against the original authoritative source.';