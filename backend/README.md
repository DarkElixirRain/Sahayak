# Sahayak Backend

**SAHAYAK — Your Voice. Your Rights. Your Protection.**

Backend for Sahayak, an AI-powered voice-first legal and safety companion
for underserved communities in Nepal.

## Current Phase

```
Phase 3C — Legal Data Ingestion (Muluki Dewani Sanhita 2074)
```

## Project

A modular FastAPI monolith designed so later phases (speech-to-text,
conversation handling, risk engine, knowledge base, Groq LLM guidance,
text-to-speech, RAG/pgvector) can be added as independent, testable
components.

The Phase 2 database is the **source of truth for legal knowledge** — the
future LLM summarises and explains it, it never generates it.

## Requirements

- Python 3.11+

## Setup

From the `backend/` directory:

```bash
python -m venv .venv
```

Activate it:

- Windows: `.venv\Scripts\activate`
- macOS/Linux: `source .venv/bin/activate`

Install dependencies:

```bash
pip install -r requirements.txt
```

Create the `.env` file:

```bash
cp .env.example .env
```

Then edit `.env` as needed.

## Environment

```env
DATABASE_URL=
GROQ_API_KEY=
APP_ENV=
LOG_LEVEL=
CORS_ORIGINS=
TEST_DATABASE_URL=       # optional: integration-test database only
```

- `DATABASE_URL` — Neon Postgres connection string. Leave empty to disable database features.
- `GROQ_API_KEY` — Groq LLM provider key (used in later phases, not Phase 2).
- `APP_ENV` — `development`, `staging`, or `production`.
- `LOG_LEVEL` — logging level, e.g. `INFO`.
- `CORS_ORIGINS` — comma-separated allowed origins.
- `TEST_DATABASE_URL` — separate database for integration tests. Never point automated tests at the real development database.

Do not commit real secret values.

## Run

From the `backend/` directory:

```bash
uvicorn app.main:app --reload
```

The server runs at http://127.0.0.1:8000

## Phase 2 — Legal Knowledge Foundation

### Architecture

The schema keeps four concerns separate:

```text
LEGAL KNOWLEDGE → laws, provisions, government resources, court cases, official sources
SAFETY / RISK   → risk rules, warning patterns, severity
CONVERSATION    → future user conversations / messages (structure only)
PROVENANCE      → where every legal fact came from (sources)
```

The LLM is never the source of truth. Every verified knowledge record is
traceable back to a `sources` row.

### Database schema

Tables (all UUID PKs, `TIMESTAMPTZ`, postgres native types, no extensions):

| table                  | purpose                                        |
|------------------------|------------------------------------------------|
| `legal_domains`        | legal situation categories (open set)          |
| `legal_documents`      | laws / codes / regulations / rules...          |
| `legal_provisions`     | sections / articles of a document (hierarchical) |
| `knowledge_chunks`     | retrieval-ready legal knowledge (no embeddings yet) |
| `sources`              | provenance of every legal fact                 |
| `government_resources` | practical "where to complain" service info     |
| `court_cases`          | verified official court decisions              |
| `risk_rules`           | deterministic scam/safety rules (structure only) |
| `conversation_sessions` / `conversation_messages` | future conversation structure |

`knowledge_chunks` deliberately has **no vector/embedding columns** yet —
it is pre-shaped so Phase 3/4 can add pgvector, hybrid and semantic retrieval.

### Migrations

Plain versioned SQL files in `app/db/migrations/`, applied by a small runner
(no ORM, no `create_all`). Each file applies once, in its own transaction.

```bash
python scripts/migrate.py
```

### Seed data

Only legal domains are seeded — never fabricated provisions or cases.

```bash
python scripts/seed_domains.py
```

### CSV format

```text
domain,document_title,document_type,provision_number,provision_title,
content,language,source_name,source_type,source_url,verified
```

Required columns: `domain`, `document_title`, `document_type`, `content`,
`source_name`, `source_url`, `verified`. Supported encodings: UTF-8 and
UTF-8 with BOM (Devanagari text is preserved exactly).

`verified` must be `true` or `false` (case-insensitive; `1`/`0` accepted).
**`verified=true` means a human checked the content against the original
authoritative source — never "the AI thinks this is correct".**

See `data/README.md` for the full reference and `data/samples/` for a
synthetic dev sample (marked `DEVELOPMENT ONLY — NOT LEGAL CONTENT`).

### Validate a CSV

```bash
python scripts/validate_legal_csv.py data/incoming/legal_knowledge.csv
```

Produces a per-row report of invalid rows (missing fields, malformed URLs,
invalid `verified`, unknown domains, short content, duplicates).

### Import a CSV

```bash
python scripts/import_legal_csv.py data/incoming/legal_knowledge.csv
```

Imports are atomic: all valid rows commit together; any database failure
rolls back everything. Matching is deterministic (domain key, document
title+type, source URL, provision number, chunk index) so re-importing the
same file **does not create duplicates**.

```bash
# import only the valid rows, report the rest
python scripts/import_legal_csv.py data/incoming/legal_knowledge.csv --best-effort
```

### Phase 3C — import the validated Muluki Dewani Sanhita 2074 dataset

The Phase 3B-validated dataset `data/legal/muluki_dewani_samhita_2074_importer_ready.csv`
(721 rows) is ingested with the standard importer:

```bash
python scripts/import_legal_csv.py data/legal/muluki_dewani_samhita_2074_importer_ready.csv
```

Behavior:

- **Atomic** — all rows import in a single transaction; any failure rolls back
  the entire import (no partial legal corpus).
- **Idempotent** — deterministic natural keys (domain key, document
  title+type, source URL, provision number, chunk index) mean re-running the
  same CSV creates no duplicates. Rows whose stored text already matches are
  skipped; provisions whose stored text is stale (e.g. a pre-correction
  import) are refreshed in place from the validated CSV.
- **Legal-text preservation** — provision and chunk content are stored
  byte-for-byte from the validated CSV. The importer never normalizes,
  corrects, or rewrites legal text.

#### Performance (why the importer was rewritten)

The original importer ran one round-trip loop per CSV row (domain lookup,
document lookup, source lookup, provision lookup, chunk lookup, plus an
insert + read-back per new row — roughly 9 statements per row, ~6,500 for this
file). That is fine against a local database but not against remote Neon,
where the first real import blew past the 300 s timeout.

`import_rows` is now **set-based** and never issues a query per row:

| phase | old | new |
|-------|-----|-----|
| prefetch existing state | per row | 5 queries (domains, sources, documents, provisions, chunks) |
| decide create / refresh / no-op | in SQL | in memory |
| writes | per row | 1 batched statement per affected table |
| **round trips for 721 rows** | **~6,500** | **8 first run / 6 on a no-op re-run** |

Measured: **19.3 s** for the first (721-row refresh) run, **6.7 s** for the
second. Transactionality, `ON CONFLICT`-safe reuse and granularity of the
skip/refresh decision are unchanged, and `ImportReport` now reports per-table
counts plus `db_operations` and `duration_seconds`, so a no-op re-import is
provably a no-op (zero writes).

#### Result for this dataset

- 3 domain-scoped `legal_documents` records: `civil` (295 provisions),
  `family` (184), `land_property` (242) — one per seeded domain referenced
  by the dataset, all titled `मुलुकी देवानी संहिता, २०७४` (type `act`)
- 721 `legal_provisions` rows and 721 `knowledge_chunks` rows
- 1 `sources` record: नेपाल कानून आयोग (Nepal Law Commission),
  `law_commission`, https://lawcommission.gov.np/content/13455/civil-code-2074
- All 721 rows stored with `is_verified = false` (the dataset's own
  verification claim — do not raise it without human re-verification)
- Section 141 carries the authorized Phase 3B correction (`व्यक्ति`); the
  legacy remnant `mव्यति` must never appear in imported content

#### Actual run (2026-09-18, Neon PostgreSQL)

The database already held a previously committed import of this document whose
provision/chunk text used `\r\n` line endings instead of the validated
dataset's `\n`. That pre-existing data was a *stale* import and was corrected
in place — this run was a refresh, not a first insert:

```text
rows 721   inserted 0   updated 721   skipped 0   failed 0
domains:    0 created, 3 reused
documents:  0 created, 3 reused
sources:    0 created, 1 reused
provisions: 0 created, 721 refreshed, 0 unchanged
chunks:     0 created, 721 refreshed
round trips 8      duration 19.27s
exit 0
```

A second identical run was a true no-op (`0 created, 0 refreshed, 721
unchanged`, 6 round trips, 6.67 s). No existing domain metadata was altered
(`land_property`'s pre-existing empty description stayed empty rather than
being invented).

> **Operational note.** The earlier timed-out import left an *orphaned*
> process holding an open transaction (`idle in transaction`, holding a
> `transactionid` lock), which silently blocked every later re-run. Before
> re-running after a timeout, check for a lingering session and confirm
> whether the transaction committed, rolled back, or is still open:
>
> ```sql
> SELECT pid, state, wait_event_type, wait_event, now() - xact_start AS xact_age, query
> FROM pg_stat_activity WHERE datname = current_database();
> ```

#### Verification procedure (read-only)

```bash
python scripts/verify_database.py            # schema, FKs, indexes
python scripts/validate_legal_csv.py data/legal/muluki_dewani_samhita_2074_importer_ready.csv
python scripts/verify_phase3c_import.py      # all 721 rows vs. the validated CSV
```

`verify_phase3c_import.py` compares every row (not a sample) and reports
counts, per-row text integrity, Section 141, referential integrity,
duplicates, domain integrity and verification state. It only runs `SELECT`s.
It passed 25/25 checks after the import and again after the idempotent
re-run: **0 provision mismatches, 0 chunk mismatches, 0 duplicates, 0
orphans**, `व्यक्ति` present at Section 141 and `mव्यति` absent everywhere.

Retrieval (`/api/knowledge/search` is relational, no RAG/embeddings):

```bash
# NOTE: imported rows are unverified, so verified=false is required today
curl --get --data-urlencode domain=family --data-urlencode q=संरक्षक \
     --data-urlencode verified=false http://127.0.0.1:8000/api/knowledge/search
curl --get --data-urlencode domain=family --data-urlencode "q=देहायका व्यक्तिहरू" \
     --data-urlencode verified=false http://127.0.0.1:8000/api/knowledge/search   # Section 141
```

The default `verified=true` filter intentionally returns nothing for this
dataset — that is a verification-policy default, not missing data. Nepali
queries match (substring); English and mixed queries return nothing because
the corpus is Nepali-only and no translation/embeddings exist yet.

### Verify the database

```bash
python scripts/verify_database.py
```

Checks the connection, all 10 tables, key indexes, and foreign keys.

### Tests

```bash
pytest                                  # unit tests (no database needed)
TEST_DATABASE_URL=... pytest            # includes integration tests
```

Integration tests only run when `TEST_DATABASE_URL` is set and always roll
back their writes. They never touch `DATABASE_URL`. They cover the Phase 3C
contract: domain reuse/creation, stale provision and chunk text refresh,
idempotency, Section 141, transaction rollback on a mid-import failure,
non-destructiveness, and a full 721-row round-trip that also asserts the
import stays set-based. A throwaway database is enough:

```bash
docker run -d --name sahayak-pg-test -e POSTGRES_PASSWORD=dev_password \
  -e POSTGRES_USER=sahayak -e POSTGRES_DB=sahayak_test -p 55432:5432 postgres:16-alpine
TEST_DATABASE_URL="postgresql://sahayak:dev_password@127.0.0.1:55432/sahayak_test" pytest
```

### Privacy

Sahayak deals with sensitive legal situations. By design (documented in
schema comments and this README) the database never stores: passwords,
OTPs, PINs, bank credentials, API keys, authentication secrets, or
unnecessary personally identifying information.

## API

```text
GET /api/health
GET /api/health/db
GET /api/system/info
GET /api/knowledge/domains
GET /api/knowledge/search?domain=consumer&q=...&verified=true&limit=20
```

- `GET /` — welcome response
- `GET /api/health` — application health
- `GET /api/health/db` — database health (`SELECT 1` against the pool)
- `GET /api/system/info` — service, environment, version (no secrets)
- `GET /api/knowledge/domains` — active legal domains (read-only)
- `GET /api/knowledge/search` — relational retrieval of knowledge chunks
  (no RAG/embeddings; read-only metadata, never legal advice)

Interactive docs:

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Project Structure

```
backend/
├── app/
│   ├── main.py                # FastAPI entry point (create_app, lifespan, CORS)
│   ├── core/
│   │   ├── config.py          # typed settings from environment
│   │   ├── logging.py         # privacy-safe logging setup
│   │   └── exceptions.py      # consistent structured error responses
│   ├── api/
│   │   ├── router.py          # central /api router
│   │   └── routes/
│   │       ├── health.py      # GET /health, GET /health/db
│   │       ├── system.py      # GET /system/info
│   │       └── knowledge.py   # read-only knowledge endpoints
│   ├── db/
│   │   ├── session.py         # psycopg pool lifecycle + health check
│   │   ├── migrate.py         # versioned SQL migration runner
│   │   ├── seed_data.py       # initial legal domains (only domains)
│   │   └── migrations/        # 001..009 versioned SQL migrations
│   ├── repositories/          # organized database access (raw SQL lives here)
│   │   ├── legal_domains.py
│   │   ├── legal_documents.py
│   │   ├── legal_provisions.py
│   │   ├── knowledge_chunks.py
│   │   ├── sources.py
│   │   ├── government_resources.py
│   │   ├── court_cases.py
│   │   └── risk_rules.py
│   ├── schemas/
│   │   ├── health.py          # Phase 1 responses
│   │   ├── system.py          # Phase 1 responses
│   │   └── knowledge.py       # read-only knowledge responses
│   ├── services/
│   │   └── csv_importer.py    # CSV validation + atomic import pipeline
│   └── models/
│       └── base.py            # base record for future persistence models
├── scripts/
│   ├── migrate.py
│   ├── seed_domains.py
│   ├── validate_legal_csv.py
│   ├── import_legal_csv.py
│   ├── verify_database.py
│   └── verify_phase3c_import.py  # read-only full-dataset verification
├── data/
│   ├── README.md              # CSV schema reference + rules
│   ├── incoming/              # real verified datasets land here (git-ignored)
│   └── samples/               # synthetic dev sample (NOT legal content)
├── tests/
│   ├── test_health.py
│   ├── test_csv_validation.py
│   ├── test_knowledge_api.py
│   ├── test_privacy.py
│   └── integration/
│       ├── test_database.py
│       └── test_phase3c_import.py  # Phase 3C regression tests
├── requirements.txt
├── .env.example
└── README.md
```

## Architecture Notes

- `schemas` = external API contracts (Pydantic)
- `services` = business logic (CSV pipeline)
- `repositories` = all database access (no raw SQL in routes)
- `models` = persistence structures (future phases)
- `db/migrations` = reproducible schema (never `create_all`)

Phase 2 deliberately does not implement AI, RAG, embeddings, pgvector,
STT/TTS, Groq, authentication, or voice processing.

## Roadmap

- Phase 3 — verified legal CSV dataset ingestion (3A/3B/3C complete)
- Phase 4 — RAG / pgvector retrieval (not yet implemented: there is no
  `POST /api/knowledge/retrieve` endpoint in this tree)
- Phase 5 — Groq guidance + risk detection
- Phase 6 — voice-to-voice (STT/TTS)