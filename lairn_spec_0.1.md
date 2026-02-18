# Liarn — Local AI Quiz Webapp (Spec for Coding Assistant)

## 0) Goal
Build a local-first webapp called **Liarn** that generates and runs quizzes to help a user learn:
- Machine Learning, Deep Learning, Statistics
- Generative AI, MLOps
- Agentic AI concepts

The app runs locally in a browser (http://localhost) and uses **Ollama** as the LLM provider to keep costs minimal. It supports **multiple-choice** and **short-answer** questions. After submission, it returns the correct answer with an explanation.

## 1) Non-goals
- No user accounts / auth in v1.
- No payments.
- No external hosted LLMs.
- No complex analytics (basic local metrics ok).

## 2) Key User Stories
1. As a learner, I can start a quiz by selecting:
   - Topics (one or many)
   - Difficulty (easy/medium/hard)
   - Question type (MCQ / short-answer / mixed)
   - Number of questions (e.g., 5/10/20)
2. As a learner, I can answer each question and submit.
3. As a learner, I immediately see:
   - Whether I was correct
   - The correct answer
   - A clear explanation
   - (Optional) a “why other options are wrong” section for MCQ
4. As a learner, I can see my results summary at the end:
   - Score, time spent, breakdown by topic
5. As a learner, I can review past quiz sessions locally (no login).

## 3) Tech Stack (Must Use)

### Backend
- Python 3.12
- FastAPI
- Pydantic v2
- Uvicorn
- Ollama as LLM provider (local)
- Storage: SQLite (local file) via SQLAlchemy OR SQLModel
- Config: pydantic-settings

### Frontend
- Vite + React + TypeScript
- UI: simple modern components (Tailwind ok; keep minimal)
- State: React Query (TanStack Query) preferred

### Containerization
- Docker + docker-compose
- Must run with one command: `docker compose up --build`
- Ollama can be:
  - Option A (preferred): external/local install on host, backend connects to it
  - Option B: run Ollama container in compose
  - Provide both modes via config

### Testing
- Backend: pytest (+ httpx TestClient for API tests)
- Frontend: vitest + @testing-library/react

## 4) Architecture Overview
- Monorepo with `backend/` and `frontend/`.
- Backend exposes REST endpoints:
  - Create quiz session (generates questions)
  - Submit an answer (evaluates and returns explanation)
  - Get session summary
  - List sessions
- LLM is used for:
  - Question generation (constrained output schema)
  - Answer evaluation and explanation (short-answer evaluation requires careful rubric)

## 5) Core Features

### 5.1 Quiz Session Flow
- A “Quiz Session” contains N questions.
- Questions are generated at session creation time and stored.
- Each question has:
  - id, type, topic tags, difficulty
  - prompt text
  - for MCQ: options[], correct_option_index
  - for short-answer: expected_answer (short), acceptable_variants[], grading_rubric (brief)
  - explanation (may be generated at creation or at evaluation)
- On submit:
  - backend evaluates correctness
  - returns result + explanation

### 5.2 Topics & Difficulty
- Topics list (v1):
  - Machine Learning
  - Deep Learning
  - Statistics
  - Generative AI
  - MLOps
  - Agentic AI
- Difficulty: easy | medium | hard
- Mixed mode: random distribution, but topic preference should be respected.

### 5.3 Scoring
- MCQ: exact match.
- Short-answer: LLM-assisted evaluation + normalization:
  - normalize user answer (trim, lowercase)
  - if matches expected/variants -> correct
  - else use LLM judge with strict rubric and require a boolean `is_correct` + short rationale
  - store judge trace for debugging (locally)

### 5.4 Local Persistence
- SQLite file persisted via Docker volume.
- Store:
  - sessions (created_at, config)
  - questions (content, correct answer, explanation)
  - answers (user_answer, is_correct, feedback)

## 6) LLM / Ollama Requirements

### 6.1 Provider
- Use Ollama HTTP API (default: `http://localhost:11434`)
- Configurable via env:
  - `OLLAMA_BASE_URL`
  - `OLLAMA_MODEL` (default suggestion: a strong free model installed via Ollama)
  - `OLLAMA_TIMEOUT_SECONDS`

### 6.2 Prompting Strategy (Important)
- Use **structured JSON outputs** for generation & evaluation.
- Enforce schema using Pydantic models.
- Use “few-shot” examples minimal.
- Implement retry with:
  - max 2 retries if JSON invalid
  - fallback: return a deterministic, non-LLM question from a small local bank so app still works

### 6.3 Safety / Quality Constraints
- Questions must be:
  - concise, unambiguous
  - not opinion-based
  - no copyrighted long text
- Explanations must be:
  - 2–6 sentences, clear, practical
- MCQ options:
  - exactly 4 options
  - only 1 correct

## 7) API Contract (REST)
Base: `/api/v1`

### 7.1 Create Session
POST `/quiz/sessions`

Request:
```json
{
  "topics": ["Machine Learning", "MLOps"],
  "difficulty": "medium",
  "question_type": "mixed",
  "num_questions": 10
}
```

Notes:
- Do NOT return correct answers in this response.

### 7.2 Submit Answer
POST /quiz/sessions/{session_id}/questions/{question_id}/answer

Request:
```json
{
  "answer": "user input (string) OR option_index for MCQ",
  "option_index": 2
}
```

Response:
```json
{
  "is_correct": true,
  "correct_answer": ".... or option text",
  "explanation": "....",
  "why_others_wrong": ["...", "...", "..."],
  "normalized_user_answer": "..."
}
```

### 7.3 Get Session Summary
GET /quiz/sessions/{session_id}/summary
Response:
```json
{
  "session_id": "uuid",
  "score": {"correct": 7, "total": 10},
  "by_topic": [{"topic":"MLOps","correct":3,"total":4}],
  "created_at": "ISO",
  "completed_at": "ISO or null"
}
```

### 7.4 List Sessions
GET /quiz/sessions?limit=20&offset=0

### 7.5 Health
GET /health
Returns:
{
  "status": "ok",
  "ollama": {"reachable": true, "model": "..." }
}

## 8) Frontend Requirements

### 8.1 Pages
Home / Setup
- topic multi-select
- difficulty selector
- question type selector
- num questions
- start button

Quiz Runner
- show one question at a time
- MCQ: radio options
- short-answer: input box
- submit -> show feedback + explanation
- next button

Results
- score summary
- breakdown by topic
- review questions with your answers + explanation

History
- list past sessions (local)
- open a session summary

### 8.2 UX Constraints
Fast and minimal
Keyboard-friendly
Show loading states when generating questions/evaluating answers
If Ollama unreachable, show clear banner with steps

## 9) Repository Layout (Target)
lairn/
  README.md
  docker-compose.yml
  .env.example
  backend/
    pyproject.toml
    app/
      main.py
      api/
      core/
      db/
      llm/
      quiz/
      schemas/
      tests/
  frontend/
    package.json
    vite.config.ts
    src/
      api/
      components/
      pages/
      routes/
      tests/

## 10) Backend Design Details

### 10.1 Modules
- app/main.py: FastAPI app + routers
- app/core/config.py: env settings
- app/db/: engine, session, models, migrations (alembic optional)
- app/llm/ollama_client.py: minimal HTTP client wrapper
- app/quiz/generator.py: question generation service
- app/quiz/grader.py: grading service (MCQ deterministic; short-answer hybrid)
- app/api/routes.py: endpoints

### 10.2 Data Models (DB)
- Session(id, created_at, completed_at, config_json)
- Question(id, session_id, type, topic, difficulty, prompt, options_json, correct_json, rubric_json, explanation)
- Answer(id, session_id, question_id, user_answer, is_correct, feedback_json, created_at)

## 11) Testing Requirements

### 11.1 Backend
Unit tests:
- JSON schema parsing from LLM outputs
- grader correctness for MCQ
- normalization logic for short answers
Integration tests:
- POST create session (with mocked Ollama)
- submit answer returns expected shape
- Provide MockOllamaServer or monkeypatch client.

### 11.2 Frontend
Component tests:
- Setup form validation
- MCQ rendering and submit
- Results page renders summary
API mocking via MSW or simple fetch mocks.

## 12) Docker / Compose

### 12.1 Services
backend: exposes 8000
frontend: exposes 5173 (or 80 via nginx)
db: not needed (SQLite volume)
ollama (optional profile)
volumes:
- sqlite db file
- ollama models (if containerized)

### 12.2 Run Commands
Dev (local):
- backend: poetry run uvicorn app.main:app --reload
- frontend: npm run dev
Container:
- docker compose up --build

## 13) Observability (Local)
Backend logs include:
- session_id, question_id
- LLM call durations
- LLM parse failures + retry count
No external telemetry.

## 14) Acceptance Criteria (Definition of Done)
User can create a quiz session and answer questions end-to-end in browser.
Works fully locally with Ollama installed.
If Ollama is not reachable, app still works with fallback question bank.
All tests pass:
- pytest
- npm test
docker compose up --build runs the full system.

## 15) Implementation Notes / Guardrails for Coding Assistant
Prefer simple, explicit code over frameworks.
Enforce strict Pydantic schemas for all LLM IO.
Keep prompts in dedicated files for maintainability.
Use UUIDs for ids.
Do not leak correct answers to frontend before submission.
Keep explanations concise.

## 16) Suggested Defaults
default topics: all
default difficulty: medium
default question type: mixed
default num_questions: 10
default model: configurable; assume user will run "ollama pull <model>" beforehand