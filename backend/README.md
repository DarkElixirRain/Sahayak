# Sahayak Backend

**SAHAYAK — Your Voice. Your Rights. Your Protection.**

Backend for Sahayak, an AI-powered voice-first legal and safety companion
for underserved communities in Nepal.

## Current Phase

```
Phase 1 — Backend Foundation
```

## Project

A modular FastAPI monolith designed so later phases (speech-to-text,
conversation handling, risk engine, knowledge base, Groq LLM guidance,
text-to-speech) can be added as independent, testable components.

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
```

- `DATABASE_URL` — Neon Postgres connection string. Leave empty to disable database features.
- `GROQ_API_KEY` — Groq LLM provider key (used in later phases, not Phase 1).
- `APP_ENV` — `development`, `staging`, or `production`.
- `LOG_LEVEL` — logging level, e.g. `INFO`.
- `CORS_ORIGINS` — comma-separated allowed origins, e.g. `http://localhost:3000,http://localhost:8080`.

Do not commit real secret values.

## Run

From the `backend/` directory:

```bash
uvicorn app.main:app --reload
```

The server runs at http://127.0.0.1:8000

## Tests

```bash
pytest
```

Tests use a planned-in dependency (FastAPI `TestClient`) and never require a
live database or Groq connection.

## API

```text
GET /api/health
GET /api/health/db
GET /api/system/info
```

- `GET /` — welcome response
- `GET /api/health` — application health
- `GET /api/health/db` — database health (`SELECT 1` against the pool)
- `GET /api/system/info` — service, environment, version (no secrets)

Interactive docs:

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Project Structure

```
backend/
├── app/
│   ├── main.py            # FastAPI app entry point (create_app, lifespan, CORS)
│   ├── core/
│   │   ├── config.py      # typed settings from environment
│   │   ├── logging.py     # privacy-safe logging setup
│   │   └── exceptions.py  # consistent structured error responses
│   ├── api/
│   │   ├── router.py      # central /api router
│   │   └── routes/
│   │       ├── health.py  # GET /health, GET /health/db
│   │       └── system.py  # GET /system/info
│   ├── db/
│   │   └── session.py     # psycopg connection pool lifecycle + health check
│   ├── models/
│   │   └── base.py        # base record for future persistence models
│   ├── schemas/
│   │   ├── health.py      # HealthResponse, DatabaseHealthResponse
│   │   └── system.py      # SystemInfoResponse
│   └── services/          # placeholder for future business-logic services
├── tests/
│   └── test_health.py
├── requirements.txt
├── .env.example
└── README.md
```

## Architecture Notes

- `schemas` = external API contracts (Pydantic)
- `services` = business logic (future phases)
- `repositories` = database access (future phases)
- `models` = persistence structures (future phases)

Phase 1 deliberately does not implement AI features, authentication, business
database tables, or voice processing.