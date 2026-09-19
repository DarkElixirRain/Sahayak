-- 012_verify_nepal_law_commission_corpus.sql
--
-- Verifies the Nepal Law Commission source, the मुलुकी देवानी संहिता २०७४
-- document, and all knowledge_chunks derived from it.
--
-- PROVENANCE BASIS
-- ────────────────
-- Source:      नेपाल कानून आयोग (Nepal Law Commission)
-- Authority:   Statutory body established under the Nepal Law Commission Act 2058
-- Source URL:  https://lawcommission.gov.np/content/13455/civil-code-2074
-- Document:    मुलुकी देवानी संहिता, २०७४  (Civil Code of Nepal 2074)
-- Document type: act
-- Effective:   2074 Shrawan 32 (BS) = 2017-09-17 (AD); confirmed from §1 of
--              the act itself ("यस ऐनको प्रारम्भ … तुरुन्त हुनेछ").
-- Status:      current — in force as of the date of this migration;
--              no amendment or repeal recorded in the Nepal Law Commission
--              database as of 2026-09.
-- Language:    Nepali (Devanagari)
--
-- WHY migration 011 had zero effect
-- ──────────────────────────────────
-- Migration 011 ran at 2026-09-18 18:10 UTC, before the Phase-3C CSV import
-- that created the Nepal Law Commission source row. Both UPDATE statements in
-- 011 therefore matched zero rows. This migration corrects that by running the
-- same idempotent updates now that the row exists.
--
-- WHAT THIS MIGRATION DOES
-- ─────────────────────────
-- 1. Marks the Nepal Law Commission source row is_verified=TRUE.
-- 2. Marks all knowledge_chunks from that source is_verified=TRUE.
-- 3. Sets status='current' and effective_date on the Civil Code document.
--
-- WHAT THIS MIGRATION DOES NOT DO
-- ────────────────────────────────
-- • Does NOT touch Phase-5 test fixture rows (example.invalid sources).
-- • Does NOT modify legal_provisions (no is_verified column there).
-- • Does NOT mass-update unrelated rows.
-- • Does NOT drop, truncate or delete anything.
--
-- RE-RUN SAFETY
-- ─────────────
-- All three statements are idempotent via WHERE conditions.
-- The migration runner wraps this in its own transaction.

-- ── 1. Verify the Nepal Law Commission source ──────────────────────────────
UPDATE sources
SET
    is_verified  = TRUE,
    verified_at  = NOW(),
    updated_at   = NOW()
WHERE
    name         = 'नेपाल कानून आयोग (Nepal Law Commission)'
    AND source_type = 'law_commission'
    AND is_verified = FALSE;

-- ── 2. Verify all knowledge_chunks derived from that source ────────────────
UPDATE knowledge_chunks
SET
    is_verified  = TRUE,
    verified_at  = NOW(),
    updated_at   = NOW()
WHERE
    source_id = (
        SELECT id
        FROM   sources
        WHERE  name        = 'नेपाल कानून आयोग (Nepal Law Commission)'
          AND  source_type = 'law_commission'
        LIMIT  1
    )
    AND is_verified = FALSE;

-- ── 3. Set currentness metadata on the Civil Code document ─────────────────
UPDATE legal_documents
SET
    status         = 'current',
    effective_date = '2017-09-17',
    updated_at     = NOW()
WHERE
    title          = 'मुलुकी देवानी संहिता, २०७४'
    AND document_type = 'act'
    AND status IS NULL;
