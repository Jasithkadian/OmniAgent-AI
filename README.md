# Veyra

Veyra is a full-stack advanced multi-agent orchestration platform. It enables you to orchestrate autonomous workflows, backed by a robust RAG (Retrieval-Augmented Generation) pipeline for document analysis and an Apple-inspired premium frontend UI.

## Features

- **Frontend**: Next.js 15 App Router, TypeScript, TailwindCSS v4, shadcn/ui, Framer Motion, and Clerk Authentication. Deep-dark mode aesthetic by default.
- **Backend**: Python FastAPI with versioned routing, Async SQLAlchemy, and CORS middleware.
- **Agents**: LangGraph multi-agent orchestration (Planning, Research, Coding, Report, Presentation).
- **RAG Pipeline**: PDF/DOCX ingestion, semantic chunking, Gemini/OpenAI embeddings, and ChromaDB persistent vector store.
- **Infrastructure**: Full Docker and docker-compose setup with PostgreSQL and ChromaDB.

## Prerequisites

- Node.js 18+
- Python 3.11+
- Docker and Docker Compose
- Clerk Account (for frontend authentication)
- Gemini API Key (or OpenAI for embeddings)

## Setup and Deployment

### 1. Environment Configuration

Copy `.env.example` to `.env` in the root directory and fill in your API keys:

```bash
cp .env.example .env
```

Important Variables to set:
- `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` & `CLERK_SECRET_KEY`
- `GEMINI_API_KEY` (or `OPENAI_API_KEY`)

### 2. Run Locally (Docker)

The easiest way to run the entire stack (Frontend, Backend, PostgreSQL Database, ChromaDB) is using Docker Compose:

```bash
docker-compose up --build
```

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Database**: Port 5432

### 3. Run Locally (Development Mode)

If you prefer to run services manually for active development:

**Backend:**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

Visit http://localhost:3000 to access the Veyra Dashboard.

## Reliability & Evaluation

Veyra includes a built-in evaluation framework to ensure high-quality, hallucination-free outputs.

### Running Benchmarks
To evaluate retrieval quality and latency:
```bash
PYTHONPATH=backend:. python3 backend/scripts/benchmark_retrieval.py
```

### Health & Metrics
Check the platform health and aggregated metrics:
- API Health: `http://localhost:8000/api/v1/health`
- Infrastructure: `http://localhost:8000/api/v1/health/db` (also `/redis`, `/vectorstore`)
- Performance Metrics: `http://localhost:8000/api/v1/health/metrics`

### Verification Agent
Every report generated is automatically audited by the `CriticAgent`. You can inspect the `verification_metrics` in the final workflow state to see the hallucination and reasoning scores.
