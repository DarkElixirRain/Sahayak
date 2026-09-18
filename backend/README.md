# Sahayak Backend

**SAHAYAK — Your Voice. Your Rights. Your Protection.**

Backend for Sahayak, an AI-powered voice-first legal and safety companion
for underserved communities in Nepal.

## Current Phase

```
Phase 2 — Legal Knowledge Database + CSV Import Foundation
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
back their writes. They never touch `DATABASE_URL`.

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
│   └── verify_database.py
├── data/
│   ├── README.md              # CSV schema reference + rules
│   ├── incoming/              # real verified datasets land here (git-ignored)
│   └── samples/               # synthetic dev sample (NOT legal content)
├── tests/
│   ├── test_health.py
│   ├── test_csv_validation.py
│   ├── test_knowledge_api.py
│   ├── test_privacy.py
│   └── integration/test_database.py
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

- Phase 3 — verified legal CSV dataset ingestion
- Phase 4 — RAG / pgvector retrieval
- Phase 5 — Groq guidance + risk detection
- Phase 6 — voice-to-voice (STT/TTS)