# PDF RAG System with Knowledge Graphs

A Retrieval-Augmented Generation (RAG) system for querying PDF documents with intelligent citations and knowledge graph integration.

## Features

- 📄 **PDF Document Processing**: Upload and query multiple PDF documents
- 🔍 **Smart Retrieval**: Vector-based semantic search with citation tracking
- 🧠 **Knowledge Graphs**: Extract and query entities and relationships
- 🤖 **Multi-Model Support**: Works with Ollama (local) and Gemini models
- 👥 **Multi-User Support**: User management with PostgreSQL database
- 🔗 **RESTful API**: Complete API endpoints for integration

## Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL with pgvector extension
- **Vector Store**: pgvector for embeddings
- **LLM**: Ollama (qwen2.5, llama3.2) / Google Gemini
- **Embeddings**: nomic-embed-text (via Ollama)
- **Cache**: Redis
- **Containerization**: Docker & Docker Compose

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Ollama (for local models)

### 1. Setup Environment

```bash
# Copy environment file
cp .env.example .env

# Edit .env and add your API keys
# GEMINI_API_KEY=your_key_here  # Optional
```

### 2. Start Services

```bash
# Start all services (PostgreSQL, Redis, API)
docker-compose up -d

# Or run locally
./start-dev.sh
```

### 3. Setup Ollama Models

```bash
# Pull required models
ollama pull qwen2.5:7b
ollama pull llama3.2
ollama pull nomic-embed-text
```

## API Usage

### Upload Document

```bash
curl -X POST "http://localhost:8000/api/ingest" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf" \
  -F "metadata={\"title\":\"My Document\"}"
```

### Query Document

```bash
curl -X POST "http://localhost:8000/api/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the main topic?",
    "k": 5
  }'
```

### Knowledge Graph Query

```bash
curl -X POST "http://localhost:8000/api/graph/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Find entities related to climate change"
  }'
```

## Project Structure

```
├── core/               # Core RAG functionality
│   ├── api.py         # API routes
│   ├── database/      # Database models
│   ├── embedding/     # Embedding models
│   ├── parser/        # Document parsers
│   ├── vector_store/  # Vector storage
│   └── services/      # Business logic
├── rag_app/           # Sample RAG application
├── scripts/           # Utility scripts
├── docker-compose.yml # Docker setup
└── morphik.toml       # Configuration
```

## Configuration

Edit `morphik.toml` to customize:

- **Models**: Switch between Ollama/Gemini models
- **Database**: PostgreSQL connection settings
- **Chunking**: Adjust chunk size and overlap
- **Knowledge Graph**: Enable/disable entity resolution

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Format code
./scripts/format.sh

# Start development server
uvicorn core.api:app --reload
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/ingest` | POST | Upload PDF document |
| `/api/query` | POST | Query documents |
| `/api/retrieve` | POST | Retrieve chunks without LLM |
| `/api/documents` | GET | List all documents |
| `/api/graph/query` | POST | Query knowledge graph |
| `/api/graph/entities` | GET | List entities |

## Environment Variables

```bash
# Database
POSTGRES_URI=postgresql://user:pass@localhost:5432/rag_db

# API Keys (optional)
GEMINI_API_KEY=your_gemini_key
OPENAI_API_KEY=your_openai_key

# JWT Secret
JWT_SECRET_KEY=your_secret_key
SESSION_SECRET_KEY=your_session_key
```

## Docker Compose Services

- **postgres**: PostgreSQL database with pgvector
- **redis**: Redis cache
- **api**: FastAPI application

## License

MIT License

## Contributing

Contributions welcome! Please open an issue or submit a pull request.
