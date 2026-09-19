-- 011_verify_muluki_dewani_samhita_chunks.sql
--
-- Verifies the Nepal Law Commission source and the 721 knowledge chunks
-- derived from the Muluki Dewani Samhita 2074 (मुलुकी देवानी संहिता, २०७४).
--
-- Provenance basis:
--   Source: नेपाल कानून आयोग (Nepal Law Commission)
--   Document: मुलुकी देवानी संहिता, २०७४
--   The CSV was derived from the official Nepal Law Commission publication
--   of the Civil Code of Nepal (Muluki Dewani Samhita), publicly available
--   at https://nepallaw.gov.np
--
-- What this migration DOES:
--   1. Marks the Nepal Law Commission source row as is_verified=TRUE
--   2. Marks all 721 knowledge_chunks sourced from that source as
--      is_verified=TRUE with verified_at timestamp
--
-- What this migration does NOT do:
--   - Does NOT verify the 3 development sample chunks
--   - Does NOT modify legal_provisions (no is_verified column there)
--   - Does NOT verify court_cases or government_resources (none exist)
--
-- Re-run safety: both statements are idempotent (WHERE is_verified = FALSE).
-- The migration runner wraps this in its own transaction; no BEGIN/COMMIT here.

-- 1. Mark the Nepal Law Commission source as verified.
UPDATE sources
SET
    is_verified = TRUE,
    verified_at = NOW(),
    updated_at  = NOW()
WHERE
    name        = 'नेपाल कानून आयोग (Nepal Law Commission)'
    AND source_type = 'law_commission'
    AND is_verified = FALSE;

-- 2. Mark all knowledge_chunks belonging to the Nepal Law Commission source
--    as verified. Development sample chunks are excluded because they belong
--    to a different source_id.
UPDATE knowledge_chunks
SET
    is_verified = TRUE,
    verified_at = NOW(),
    updated_at  = NOW()
WHERE
    source_id = (
        SELECT id
        FROM   sources
        WHERE  name        = 'नेपाल कानून आयोग (Nepal Law Commission)'
          AND  source_type = 'law_commission'
        LIMIT  1
    )
    AND is_verified = FALSE;
