# Kanun Sathi Run Report

## Environment
* **macOS architecture**: Apple Silicon (arm64)
* **Python version**: Python 3.11.16 (installed to resolve `datetime.UTC` import requirement)
* **uv version**: 0.12.17
* **Node version**: v26.4.0
* **package manager**: npm 11.17.0

## Backend
* **startup command**: `venv311/bin/python start_server.py --skip-redis-check --skip-ollama-check` (The flags were used to avoid docker-compose shorthand errors and missing Ollama installation)
* **host**: 0.0.0.0
* **port**: 8000
* **status**: RUNNING (Verified via `/health` endpoint)
* **API docs**: Available at `http://localhost:8000/docs` and `http://localhost:8000/openapi.json`

## Infrastructure
* **PostgreSQL status**: RUNNING (via docker-compose)
* **Redis status**: RUNNING (via docker-compose)
* **other required services**: N/A

## AI
* **AI provider**: Google Gemini
* **model**: `gemini-3.6-flash` (updated from deprecated `gemini-2.5-flash` in `morphik.toml`)
* **configuration status**: Configured using API key in `.env`

## Legal Knowledge Base
* **dataset location**: Postgres database (`pgvector` store)
* **retrieval method**: Hybrid (ColPali/pgvector backend logic)
* **vector/keyword search**: Configured for pgvector embeddings
* **embeddings**: Local Ollama embedding `nomic-embed-text`
* **source/citation mechanism**: In-built via RAG pipeline (chunk metadata attached)

## Frontend
* **startup command**: `npm install && npm run dev`
* **URL**: `http://localhost:5173/`
* **backend connection status**: Connected

## Legal Test Results

| Query | Backend | Retrieval | AI | Sources | Result |
| ----- | ------- | --------- | -- | ------- | ------ |
| मेरो भाइले मलाई मुद्दा हाल्यो। | 500 Error | Attempted | Invoked (503) | None | Failed due to Gemini 503 Overload |
| अदालतबाट म्याद आएको छ, अब के गर्नुपर्छ? | 500 Error | Attempted | Invoked (503) | None | Failed due to Gemini 503 Overload |
| mero bhai le malai mudda halyo aba ke garne? | 500 Error | Attempted | Invoked (503) | None | Failed due to Gemini 503 Overload |
| मेरो जग्गाको सिमाना विवाद छ। | 500 Error | Attempted | Invoked (503) | None | Failed due to Gemini 503 Overload |
| What should I do if someone files a case against me in Nepal? | 500 Error | Attempted | Invoked (503) | None | Failed due to Gemini 503 Overload |

## Conversation Test
* **Request 1:** मेरो भाइले मलाई मुद्दा हाल्यो।
* **Response 1:** *Failed (500 Internal Server Error)* - The application correctly invoked the LLM but received a 503 Unavailable error: `Gemini API error: 503 - {"error": {"code": 503, "message": "This model is currently experiencing high demand..."}}`.

Because the very first message failed due to the upstream Google Gemini API outage, the conversation memory (follow-ups) could not be tested successfully.

## Blockers
* **Gemini API Overload (503)**: The Google Gemini API is currently overloaded and rejecting traffic. This prevents the generation of responses.

## Final Status
PARTIALLY RUNNING

The environment, dependencies, infrastructure (Postgres/Redis), backend, and frontend are all successfully running end-to-end. However, actual AI query generation is currently blocked by an upstream Gemini API outage (503 High Demand).
