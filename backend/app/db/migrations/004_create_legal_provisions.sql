-- 004_create_legal_provisions.sql
-- Individual sections/articles/rules/chapters/schedules within a document.
-- parent_id allows hierarchy (nested subsections) when the source has them.

CREATE TABLE IF NOT EXISTS legal_provisions (
    id               UUID PRIMARY KEY,
    document_id      UUID NOT NULL REFERENCES legal_documents(id) ON DELETE CASCADE,
    parent_id        UUID REFERENCES legal_provisions(id) ON DELETE SET NULL,
    provision_number VARCHAR(128),
    title            VARCHAR(512),
    text             TEXT NOT NULL,
    language         VARCHAR(32),
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_legal_provisions_document_id ON legal_provisions (document_id);
CREATE INDEX IF NOT EXISTS idx_legal_provisions_parent_id ON legal_provisions (parent_id);

-- A provision number is unique within its document (when one is given).
CREATE UNIQUE INDEX IF NOT EXISTS uq_legal_provisions_document_number
    ON legal_provisions (document_id, provision_number)
    WHERE provision_number IS NOT NULL;

COMMENT ON TABLE legal_provisions IS
    'Individual provisions of a legal document. provision_number is free text '
    '(Section 1, Article 3, Rule 4, Chapter X, Schedule...) — never assume numeric.';
COMMENT ON COLUMN legal_provisions.text IS
    'Original wording of the provision as taken from the verified source.';