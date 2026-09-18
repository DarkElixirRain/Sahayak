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

Then edit `.env` as needed.

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

## Project Structure

```
backend/
├── app/
│   ├── main.py            # FastAPI app, CORS, root endpoint
│   ├── config.py          # Settings loaded from .env
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
- RAG / legal knowledge base
- PostgreSQL + pgvector
- Speech-to-text
- Text-to-speech
- Risk detection
- Voice/chat endpoints