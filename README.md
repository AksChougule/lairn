# Lairn

Lairn is a local-first quiz trainer for AI/ML topics. It lets users generate quiz sessions, answer MCQ and short-answer questions, get immediate feedback, and review past performance.

The project exists to provide a practical learning loop:
1. Generate focused questions by topic and difficulty.
2. Answer and receive explanations.
3. Track progress across sessions.

## Key Features

- Quiz session creation from selected topics, difficulty, and question type.
- Supports `mcq`, `short-answer`, and `mixed` sessions.
- LLM-powered question generation through Ollama.
- Backend deduplication so prompts are unique within a session.
- Short-answer grading with:
  - normalization and variant matching,
  - LLM judge pass,
  - deterministic fallback when LLM output is unusable.
- Session scoring, topic breakdown, and session history.
- Health endpoint with Ollama availability status.
- Swagger docs via FastAPI OpenAPI UI.

## Tech Stack

- Backend:
  - FastAPI
  - SQLModel / SQLAlchemy
  - SQLite
  - Pydantic v2
  - Httpx
  - Poetry
- LLM:
  - Ollama (default model: `qwen3:1.7b`)
- Frontend:
  - React 19 + TypeScript
  - Vite
  - TanStack React Query
  - Axios
- Testing:
  - Backend: Pytest
  - Frontend unit/component: Vitest + Testing Library
  - E2E: Playwright

## Architecture Overview

High-level flow:

`User -> React frontend -> FastAPI backend -> Ollama -> FastAPI -> React -> User`

- Frontend collects quiz config and calls backend REST endpoints.
- Backend validates requests, generates/evaluates quiz content, and persists session data in SQLite.
- Ollama is used for JSON-structured generation and grading assistance.
- Frontend displays live quiz, feedback, summary, and history.

See `SYSTEM_WORKFLOW.md` for a full step-by-step flow and file mapping.

## Prerequisites

- Python `3.12`
- Poetry
- Node.js `20+` (current repo also works with newer versions)
- npm
- Ollama installed and running
- Ollama model pulled (default: `qwen3:1.7b`)

## Setup

### 1) Backend Setup

```bash
cd backend
poetry install
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend base URL: `http://localhost:8000`

Swagger docs:
- `http://localhost:8000/docs`
- `http://localhost:8000/redoc`

### 2) Frontend Setup

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend URL (default): `http://localhost:5173`

The Vite proxy (`frontend/vite.config.ts`) forwards:
- `/api` -> `http://localhost:8000`
- `/health` -> `http://localhost:8000`

### 3) Ollama Setup

Install and start Ollama, then pull the configured model:

```bash
ollama pull qwen3:1.7b
ollama list
```

Optional health check:

```bash
curl http://localhost:11434/api/tags
curl http://localhost:8000/health
```

## Running Tests

### Backend

```bash
cd backend
poetry run pytest
```

### Frontend Unit/Component

```bash
cd frontend
npm test
```

### Frontend E2E

```bash
cd frontend
npx playwright test
```

## Common Troubleshooting

### SQLite: `unable to open database file`

- Confirm backend is started from `backend/` when using default DB URL (`sqlite:///./lairn.db`).
- If using `sqlite_path` in `.env`, ensure directory exists and is writable.
- Check current DB settings in `backend/app/core/config.py`.

### SQLite schema mismatch (example: missing column)

- This usually means an old DB file with stale schema.
- Remove or back up local DB file and restart backend so tables are recreated.

### Port already in use

- Backend: change `--port` in uvicorn command.
- Frontend: `npm run dev -- --port <port>`.
- Update proxy/base URLs if needed.

### Ollama not reachable / model unavailable

- Ensure Ollama daemon is running.
- Confirm model exists with `ollama list`.
- Pull missing model: `ollama pull qwen3:1.7b`.
- Verify backend health endpoint: `GET /health`.

### Frontend cannot call API

- Ensure backend is running at `http://localhost:8000`.
- Ensure frontend is running via Vite dev server with configured proxy.

## Project Structure Summary

```text
lairn/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routes
│   │   ├── quiz/         # Generation + grading domain logic
│   │   ├── llm/          # Ollama client integration
│   │   ├── db/           # SQLModel models and DB session/engine
│   │   ├── schemas/      # Request/response contracts
│   │   └── tests/        # Backend tests
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── pages/        # Setup/Runner/Results/History UI
│   │   ├── components/   # Shared UI pieces
│   │   ├── api/          # API client + endpoint functions
│   │   ├── constants/    # Topic value/label mapping
│   │   └── types/        # API TypeScript types
│   └── tests/e2e/        # Playwright tests
├── lairn_spec_0.1.md
├── SYSTEM_WORKFLOW.md
└── PROJECT_STRUCTURE.md
```

## API Endpoints (Current)

- `POST /api/v1/quiz/sessions`
- `POST /api/v1/quiz/sessions/{session_id}/questions/{question_id}/answer`
- `GET /api/v1/quiz/sessions/{session_id}/summary`
- `GET /api/v1/quiz/sessions`
- `GET /health`
