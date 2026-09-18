# Sahayak Backend

Backend for **Sahayak**, an AI-powered voice-based rights and safety assistant.

Built with Python 3.11+ and FastAPI.

## Tech Stack

- Python 3.11+
- FastAPI
- Uvicorn
- Pydantic
- python-dotenv

## Getting Started

### 1. Create a virtual environment

From the `backend/` directory:

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

### 2. Install requirements

```bash
pip install -r requirements.txt
```

### 3. Create the `.env` file

```bash
cp .env.example .env
```

Then edit `.env` as needed. For Neon Postgres, set `DATABASE_URL` to your project's connection string, e.g.:

```
DATABASE_URL=postgresql://USER:PASSWORD@HOST.us-east-2.aws.neon.tech/DATABASE?sslmode=require
```

The backend connects to the database through a psycopg connection pool initialized on startup. The app relies on `DATABASE_URL`; if it is empty the pool is skipped.

### 4. Run the FastAPI server

```bash
uvicorn app.main:app --reload
```

The server runs at http://127.0.0.1:8000

### 5. Open the Swagger API documentation

Visit http://127.0.0.1:8000/docs in your browser.

You can also use:

- ReDoc: http://127.0.0.1:8000/redoc
- Root endpoint: http://127.0.0.1:8000/
- Health check: http://127.0.0.1:8000/api/health
- Database check: http://127.0.0.1:8000/api/health/db

## Project Structure

```
backend/
├── app/
│   ├── main.py            # FastAPI app, CORS, root endpoint, lifespan
│   ├── config.py          # Settings loaded from .env
│   ├── db.py              # psycopg connection pool
│   ├── api/
│   │   └── routes.py      # API routes
│   ├── schemas/
│   │   └── health.py      # Pydantic response models
│   └── services/
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Roadmap

Future additions planned:

- Groq LLM integration
- RAG / legal knowledge base (pgvector)
- Speech-to-text
- Text-to-speech
- Risk detection
- Voice/chat endpoints