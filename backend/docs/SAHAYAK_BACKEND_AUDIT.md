# Sahayak Backend — Complete Audit

**Generated:** 2026-09-18  
**Auditor:** Backend Engineering  
**Baseline:** 325 tests passing, 67 skipped (integration), 0 failing

---

## 1. Architecture

### Framework
- **FastAPI** (>=0.115.0) with Pydantic v2 schemas
- **Uvicorn** ASGI server
- **Python 3.12** (`.python-version` pinned)

### Database
- **PostgreSQL** hosted on **Neon** (serverless Postgres)
- Driver: **psycopg 3** (`psycopg[binary]>=3.2.0`)
- Connection pool: **psycopg-pool** (`min_size=1, max_size=5`)
- No ORM. All queries are raw parameterised SQL.

### Database Layer Pattern
- **Repository pattern**: each table has a dedicated repository class
- `BaseRepository` provides `_fetch_all`, `_fetch_one`, `_execute`, `_execute_returning`, `_executemany`
- All repositories accept an open connection (no auto-connection per method)
- `get_connection()` context manager from `app.db.session` provides pooled connections
- `DatabaseUnavailableError` (HTTP 503) raised when pool is None or query fails

### API Structure
```
/api/health                               GET  - liveness probe
/api/health/db                            GET  - database connectivity check
/api/system/info                          GET  - service/version info (no secrets)
/api/knowledge/domains                    GET  - list legal domains
/api/knowledge/search                     GET  - keyword search of chunks
/api/knowledge/retrieve                   POST - ranked legal retrieval
/api/conversations/{session_id}/messages  POST - send a message (main conversation endpoint)
/api/conversations/{session_id}           GET  - get session state + history
```

### Authentication & Authorization
- **NONE currently implemented**. No JWT, no API keys, no rate limiting.
- This is a significant production gap.
- All endpoints are publicly accessible.

### CORS
- Configured via `CORS_ORIGINS` env variable
- Default: `http://localhost:3000,http://localhost:8080`
- `allow_credentials=True, allow_methods=["*"], allow_headers=["*"]`

### Background Jobs
- **None**. No Celery, no cron, no async tasks.

### AI / LLM Layer
- Provider abstraction: `OpenAICompatibleProvider` wrapping any OpenAI-compatible endpoint
- Default provider: **Groq** (`https://api.groq.com/openai/v1`)
- Process-level cached provider instance (`_provider_cache`)
- **CRITICAL BUG**: `LLM_MODEL` defaults to `openai/gpt-oss-120b` which is **NOT** a valid Groq model
- Configured via: `LLM_PROVIDER`, `LLM_API_KEY`, `LLM_MODEL`, `LLM_BASE_URL`, `LLM_TIMEOUT_SECONDS`
- Falls back gracefully when not configured (returns `llm_unavailable` response)

### Retrieval Architecture
- **Lexical/ILIKE** only — no embeddings, no pgvector, no full-text search
- Multi-term OR matching: any token matches → candidate
- Scoring: `(content_hits/n)*1.0 + (title_hits/n)*0.3 + domain_match*0.1` (max 1.4)
- `verified_only=True` is default and enforced for authoritative answers
- Token regex handles Devanagari combining marks correctly

### Legal Knowledge Architecture
```
sources → legal_documents → legal_provisions → knowledge_chunks
legal_domains ← legal_documents
legal_domains ← knowledge_chunks (denormalised for retrieval)
sources ← knowledge_chunks (denormalised for provenance)
```

---

## 2. Database

### Tables

| Table | Purpose | Row Count |
|-------|---------|-----------|
| `legal_domains` | Legal subject-matter categories | 13 |
| `sources` | Provenance/authority sources | 3 (2 duplicates!) |
| `legal_documents` | Laws, codes, acts | 5 (3 duplicates!) |
| `legal_provisions` | Individual sections/articles | 724 |
| `knowledge_chunks` | Retrieval-ready pieces | 724 |
| `conversation_sessions` | User sessions | 24 |
| `conversation_messages` | Turn-by-turn messages | 102 |
| `government_resources` | Practical service info | 0 |
| `court_cases` | Verified court decisions | 0 |
| `risk_rules` | Safety detection rules | 0 |

### Schema Details

**legal_domains**
- `id UUID PK`, `key VARCHAR(64) UNIQUE`, `name`, `description`, `is_active`, timestamps
- Seeded with 13 domains: civil, family, land_property, inheritance, employment, consumer, cyber, banking, criminal, government_services, court_procedure, safety, other

**sources**
- `id UUID PK`, `name`, `source_type`, `organization`, `official_url` (UNIQUE when non-null), `is_official`, `is_verified`, `verified_at`
- **BUG**: 2 rows with identical `name='Development Sample Source'` and `source_type='official_document'` (no URL to constrain uniqueness)
- Nepal Law Commission row: `is_verified=FALSE` (should be TRUE for an authoritative source)

**legal_documents**
- `id UUID PK`, `domain_id FK`, `title`, `short_title`, `document_type`, `jurisdiction`, `issuing_authority`, `official_source_url`, `language`, `effective_date`, `status`
- Unique constraint: `(domain_id, title, document_type)` — same law can exist per domain
- **BUG**: 3 rows of `मुलुकी देवानी संहिता, २०७४` (for inheritance, land_property, civil domains) — 3× the provisions
- **BUG**: 2 development sample documents remain in the database

**legal_provisions**
- `id UUID PK`, `document_id FK (CASCADE)`, `parent_id FK (self-referential)`, `provision_number`, `title`, `text NOT NULL`, `language`
- Unique: `(document_id, provision_number)` when provision_number is not null
- No `is_verified` — verification lives at the chunk level (by design)

**knowledge_chunks**
- `id UUID PK`, `document_id FK (CASCADE)`, `provision_id FK (SET NULL)`, `domain_id FK`, `source_id FK`, `title`, `content NOT NULL`, `language`, `chunk_index`, `source_type`, `is_verified BOOLEAN DEFAULT FALSE`, `verified_at`
- Unique: `(document_id, COALESCE(provision_id, null_uuid), chunk_index, COALESCE(language, ''))`
- **CRITICAL BUG**: ALL 724 chunks have `is_verified=FALSE`. Every query with `verified_only=True` returns nothing.

**conversation_sessions**
- `id UUID PK`, `session_id UUID UNIQUE NOT NULL`, `status`, `language`, `started_at`, `updated_at`, `ended_at`
- **Note**: `session_id` column is `UUID` type. The repository maps any string through `uuid5` for non-UUID keys.

**conversation_messages**
- `id UUID PK`, `session_id UUID FK → conversation_sessions.id`, `role CHECK(user/assistant/system)`, `input_mode CHECK(voice/text)`, `content`, `created_at`
- Messages use `clock_timestamp()` not `now()` to avoid same-transaction timestamp collisions

### Migrations Applied (9/9)
```
001_create_legal_domains.sql
002_create_sources.sql
003_create_legal_documents.sql
004_create_legal_provisions.sql
005_create_knowledge_chunks.sql
006_create_government_resources.sql
007_create_court_cases.sql
008_create_risk_rules.sql
009_create_conversation_tables.sql
```

### Indexes
All expected indexes are present. Key ones:
- `idx_knowledge_chunks_is_verified` — critical for verified_only queries
- `idx_knowledge_chunks_domain_id` — domain-filtered retrieval
- `uq_knowledge_chunks_doc_prov_idx_lang` — idempotent imports
- `uq_legal_documents_domain_title_type` — idempotent imports

---

## 3. Legal Knowledge

### Sources (3 rows)
1. `Development Sample Source` (`official_document`, `is_verified=FALSE`) — DEV ONLY
2. `Development Sample Source` (**DUPLICATE**, same type, no URL) — DEV ONLY
3. `नेपाल कानून आयोग (Nepal Law Commission)` (`law_commission`, `is_verified=FALSE`)

**Issues:**
- Nepal Law Commission source is not marked verified despite being authoritative
- Two duplicate development sample sources

### Documents (5 rows)
1. `Development Sample Act` — `rule=act`, dev-only content
2. `Development Land Sample Rule` — `type=rule`, dev-only content
3. `मुलुकी देवानी संहिता, २०७४` → domain: `inheritance`
4. `मुलुकी देवानी संहिता, २०७४` → domain: `land_property`
5. `मुलुकी देवानी संहिता, २०७४` → domain: `civil`

**Issues:**
- Same law imported 3× (once per domain) — 3× more provisions/chunks than needed
- Dev sample documents remain in database

### Provisions (724 rows)
- Mix of dev samples (small number) + Muluki Dewani Samhita provisions (majority)
- Content is in Nepali (Devanagari)
- No `is_verified` column (by design — verification is at chunk level)

### Knowledge Chunks (724 rows)
- **ALL 724 are `is_verified=FALSE`**
- The CSV import set `is_verified=False` for every row
- The Muluki Dewani Samhita CSV data has `verified=false` in the source CSV
- This means the primary authoritative corpus is completely unretrievable for grounded answers

### Verification State
- **0 verified chunks** out of 724
- Consequence: every `GET /api/knowledge/search?verified=true` returns empty
- Consequence: every `POST /api/knowledge/retrieve` with `verified_only=true` returns no results
- Consequence: every conversation response has `status=no_match` (since no verified chunks exist)
- Consequence: grounded generation never fires

### Legal Currentness
- `legal_documents.effective_date` and `status` fields exist but are NULL for all rows
- No amendment or repeal metadata populated

---

## 4. Conversation Engine

### Architecture
- `ConversationService` class with question analysis, retrieval, generation pipeline
- Sessions stored in `conversation_sessions` table
- Messages stored in `conversation_messages` table
- History fetched per turn (last N messages)

### Case Context
- `CaseContext` dataclass with 22 fields (user_role, opposing_party, matter_type, etc.)
- `CaseContextManager` holds a `dict[session_id → CaseContext]` **in memory**
- **CRITICAL**: Context is process-local, lost on restart, incompatible with multi-worker deployments
- Each `ConversationService()` instance creates its own `CaseContextManager()` — in a web server context this means **each request creates a fresh manager with no history**

### Memory
- Multi-turn history IS persisted in PostgreSQL via `conversation_messages`
- `get_recent_context(max_messages=10)` fetches and passes to LLM
- **But**: structured case context is only in-memory, not in the database

### Follow-up Questions
- Generated from `CaseContextManager.get_missing_fields()`
- Because `CaseContextManager` is fresh per request, all fields appear "missing" on every turn
- Result: repetitive follow-up questions on every turn, regardless of what user already said
- `default_follow_up_questions()` always adds 3 generic questions

### Issue Classification
- Intent classification via keyword matching (`_classify_intent`)
- Domain extraction via intent map + keyword patterns
- Entity extraction: basic word tokenization
- No ML-based classification

### Query Reformulation
- No explicit query reformulation beyond extracting the domain
- The user's raw query string is passed directly to `retrieve_legal_context`
- Case context is not used to enrich the retrieval query

---

## 5. AI

### LLM Abstraction
- `LLMProvider` abstract base class
- `OpenAICompatibleProvider` concrete implementation
- Configurable: provider, model, base URL, API key, timeout
- Process-level singleton via `get_llm_provider()` / `_provider_cache`

### Provider Configuration
- `LLM_PROVIDER=groq` (default)
- `LLM_MODEL=openai/gpt-oss-120b` **(BROKEN — not a Groq model)**
- `LLM_API_KEY` / `GROQ_API_KEY` (both populated in .env)
- Timeout: 30 seconds

### Prompt Architecture
- System prompt: strict grounding rules (7 rules), language instruction, verification note
- Context block: fenced `<legal_context>...</legal_context>` with sanitized provision text
- User message wrapper: "Answer using only the legal context in your instructions"
- Prompt injection defense: `_FENCE_RE` strips fence tags from retrieved content

### Grounding
- Retrieved verified provisions → context block → system prompt
- Citations built from DB rows BEFORE generation (never from model output)
- Model asked to list sources by name/section in its answer
- No verification that the model actually used the cited sources (LLM can still hallucinate within the prompt)

### Citation Generation
- `build_citations(results)` creates citation dicts from retrieval rows
- Fields: `document`, `document_id`, `section`, `section_title`, `provision`, `provision_id`, `chunk_id`, `chunk_index`, `domain`, `source`, `source_url`, `is_verified`, `score`
- **All fields from database rows — no LLM-invented citations**

### Fallback Behavior
- `llm_unavailable`: model generates `STATUS_LLM_UNAVAILABLE` response with real citations
- `no_match`: honest "no verified provision found" message in user's language
- `no_verified_context`: "found but unverified" message
- `retrieval_error`: "knowledge base unreachable" message

---

## 6. Tests

### Unit Tests (325 passing)
| File | Tests | Focus |
|------|-------|-------|
| `test_health.py` | 8 | Health/system endpoints, error handling |
| `test_conversation.py` | ~35 | ConversationService, schema conformance |
| `test_conversation_llm.py` | ~40 | LLM provider, generation |
| `test_legal_grounding.py` | ~45 | Prompt building, citations, fallbacks |
| `test_llm.py` | ~30 | LLM abstraction, error types |
| `test_retrieval.py` | ~50 | Retrieval API endpoint validation |
| `test_retrieval_lexical.py` | ~30 | Tokenizer, scoring weights |
| `test_security.py` | ~45 | SQL injection, prompt injection, secrets |
| `test_knowledge_api.py` | ~8 | Knowledge endpoints |
| `test_csv_validation.py` | ~20 | CSV importer validation |
| `test_legacy_nepali.py` | ~15 | Legacy encoding conversion |
| `test_legal_dataset_audit.py` | ~10 | Dataset audit script |
| `test_privacy.py` | ~3 | Disclaimer content |

### Integration Tests (67 skipped — require `TEST_DATABASE_URL`)
| File | Tests | Focus |
|------|-------|-------|
| `test_database.py` | 11 | Schema, constraints, repo operations |
| `test_phase3c_import.py` | 10 | CSV import idempotency |
| `test_phase4_retrieval.py` | 24 | End-to-end retrieval against real DB |
| `test_phase5_conversation.py` | 22 | Conversation engine against real DB |

### E2E Tests
- None exist as standalone; the 6-turn scenario is tested manually via `test_6turn_conversation.py` (root level)

### Skipped Test Root Cause
All 67 integration tests are skipped because `TEST_DATABASE_URL` environment variable is not set. They are NOT broken — they require a separate test database to run.

---

## 7. Critical Issues Summary

### CRITICAL (blocks core functionality)

1. **All 724 knowledge chunks unverified** — every grounded answer returns `no_match`/`no_verified_context`. The entire grounded generation pipeline never fires.

2. **LLM model misconfigured** — `openai/gpt-oss-120b` is not a valid Groq model. Even if verified chunks existed, generation would fail with HTTP 404.

3. **CaseContextManager is in-memory per-request** — `ConversationService()` creates a new `CaseContextManager()` on every instantiation. Since the route creates a new `ConversationService()` per request, case context is never shared between turns. The canonical 6-turn scenario cannot accumulate context.

### HIGH (significantly degrades functionality)

4. **No query reformulation** — raw user query goes to retrieval without enrichment from case context, prior turns, or legal terminology expansion.

5. **Follow-up questions always generic** — because case context is fresh per request, all fields appear "missing" and the same 3 generic questions are suggested on every turn.

6. **Duplicate Muluki Dewani Samhita** — 3 copies across 3 domains means ~240 provisions each appear 3 times. Retrieval returns 3 copies of the same result.

7. **No authentication/authorization** — all endpoints publicly accessible.

### MEDIUM

8. **Duplicate development source** — `Development Sample Source` has 2 rows.

9. **Dev sample data in DB** — "DEVELOPMENT ONLY" content lives alongside real law.

10. **Nepal Law Commission source not marked verified** — `is_verified=FALSE` even though it's authoritative.

11. **Missing conversation context persistence** — `case_context` fields not stored in database.

12. **No rate limiting** — endpoints accept unlimited requests.

### LOW

13. **No effective_date/status** on documents — legal currentness cannot be established.

14. **LLM cannot verify it cited the right sources** — it receives citations pre-built but may not reference them correctly in its answer.

15. **conversation_sessions.session_id is UUID type** — all free-text session keys work via uuid5 mapping, but this is invisible to clients and could cause confusion.
