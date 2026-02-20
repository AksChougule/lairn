# SYSTEM_WORKFLOW

This document explains Lairn's end-to-end runtime flow and maps each step to the backend/frontend files that implement it.

## 1) High-Level Request Flow

1. User interacts with the React UI (`frontend/src/App.tsx` + page components).
2. Frontend sends HTTP requests through `frontend/src/api/client.ts` and `frontend/src/api/quiz.ts`.
3. FastAPI routes in `backend/app/api/quiz.py` process requests.
4. Backend domain services call:
   - `backend/app/quiz/generator.py` for question generation,
   - `backend/app/quiz/evaluator.py` for short-answer grading.
5. LLM calls are made through `backend/app/llm/ollama.py`.
6. SQLModel persists and retrieves data via:
   - `backend/app/db/models.py`,
   - `backend/app/db/session.py`.
7. Backend returns response DTOs from `backend/app/schemas/quiz.py`.
8. Frontend updates local/UI state and renders feedback to user.

## 2) Flow A: Creating a Quiz Session

### Sequence

1. User fills Setup form in `frontend/src/pages/SetupPage.tsx`:
   - topics,
   - difficulty,
   - question type,
   - number of questions (max 15 in UI).
2. `SetupPage` calls `onStart(payload)` in `frontend/src/App.tsx`.
3. `App.tsx` triggers React Query mutation `createSessionMutation`.
4. API call goes through `createQuizSession()` in `frontend/src/api/quiz.ts`:
   - `POST /api/v1/quiz/sessions`.
5. FastAPI route `create_quiz_session()` in `backend/app/api/quiz.py` receives `CreateQuizSessionRequest`.
6. Request validation is enforced by `backend/app/schemas/quiz.py`:
   - `num_questions` is `ge=1, le=15`.
7. Route calls `generate_questions()` in `backend/app/quiz/generator.py`.
8. `generate_questions()`:
   - builds a strict JSON prompt,
   - calls Ollama via `ollama_client.generate_json()`,
   - validates question shapes,
   - falls back to deterministic topic bank if needed,
   - deduplicates prompts with `_deduplicate_questions()`.
9. Dedup behavior:
   - prompt normalization via `_normalize_prompt()`,
   - duplicate-only regeneration via `_regenerate_duplicate_question()`,
   - if still duplicate after retries, unique prompt suffix is added to duplicate only.
10. Route persists session + questions with SQLModel (`QuizSession`, `QuizQuestion`).
11. API returns `CreateQuizSessionResponse` (public question fields only).
12. Frontend mutation success handler in `App.tsx`:
    - stores session,
    - resets previous answers,
    - sets current index to 0,
    - switches to Quiz Runner view.

### Backend files involved

- `backend/app/api/quiz.py`
- `backend/app/quiz/generator.py`
- `backend/app/llm/ollama.py`
- `backend/app/db/models.py`
- `backend/app/db/session.py`
- `backend/app/schemas/quiz.py`

### Frontend files involved

- `frontend/src/pages/SetupPage.tsx`
- `frontend/src/App.tsx`
- `frontend/src/api/quiz.ts`
- `frontend/src/types/api.ts`
- `frontend/src/constants/topics.ts`

## 3) Flow B: Submitting an Answer (MCQ)

### Sequence

1. Quiz Runner renders current question in `frontend/src/pages/QuizRunnerPage.tsx`.
2. User selects a radio option and submits.
3. `QuizRunnerPage` calls `onSubmitAnswer(question, { option_index })`.
4. `App.tsx` `submitMutation` calls `submitAnswer()` API function.
5. Request goes to:
   - `POST /api/v1/quiz/sessions/{session_id}/questions/{question_id}/answer`.
6. Backend `submit_answer()` in `backend/app/api/quiz.py`:
   - loads session and question,
   - checks for previously stored answer (idempotent return path),
   - validates `option_index` for MCQ,
   - computes correctness by comparing with `correct_option_index`,
   - builds `why_others_wrong` entries,
   - stores `QuizAnswer` row.
7. If answered count reaches `num_questions`, backend sets session `completed_at`.
8. Backend returns `SubmitAnswerResponse`.
9. Frontend stores answer record in local state and renders correctness + explanation.

### Backend files involved

- `backend/app/api/quiz.py`
- `backend/app/db/models.py`
- `backend/app/db/session.py`

### Frontend files involved

- `frontend/src/pages/QuizRunnerPage.tsx`
- `frontend/src/App.tsx`
- `frontend/src/api/quiz.ts`

## 4) Flow C: Submitting a Short-Answer

### Sequence

1. User enters free text in `QuizRunnerPage.tsx` and submits.
2. Frontend sends payload `{ answer: string }` to same answer endpoint.
3. Backend `submit_answer()` validates required short-answer fields exist on the question.
4. Backend calls `evaluate_short_answer()` from `backend/app/quiz/evaluator.py`.

### Grading path in `evaluate_short_answer()`

1. Normalize strings with `normalize_answer()` (lowercase, strip punctuation, collapse whitespace).
2. Deterministic exact/contains checks:
   - contains match between normalized user and expected answer,
   - exact match or acceptable variant match.
3. If deterministic checks fail, call LLM judge through `ollama_client.generate_json()` with strict schema:
   - `{"is_correct": boolean, "rationale": string}`.
4. Ollama client retry behavior (`backend/app/llm/ollama.py`):
   - retries parse/validation/network failures (`max_retries=2` in current usage).
5. If judge still fails or returns unusable result, fallback to `_deterministic_fallback()`:
   - token-overlap scoring,
   - deterministic explanation (never generic "could not verify" fallback text).
6. Backend returns structured `SubmitAnswerResponse` explanation and correctness.

### Backend files involved

- `backend/app/api/quiz.py`
- `backend/app/quiz/evaluator.py`
- `backend/app/llm/ollama.py`

### Frontend files involved

- `frontend/src/pages/QuizRunnerPage.tsx`
- `frontend/src/App.tsx`
- `frontend/src/api/quiz.ts`

## 5) Flow D: Viewing Summary and History

### D1) Session summary after quiz

1. After final question, user clicks `Finish Quiz` in `QuizRunnerPage.tsx`.
2. `App.tsx` switches active view to `results`.
3. React Query `summaryQuery` in `App.tsx` becomes enabled.
4. Frontend calls `GET /api/v1/quiz/sessions/{session_id}/summary`.
5. Backend `get_session_summary()` computes totals via `_calc_summary()`.
6. `ResultsPage.tsx` renders score, by-topic breakdown, and review content.

### D2) Session history view

1. User opens History tab (`frontend/src/components/NavTabs.tsx`).
2. `HistoryPage.tsx` queries `GET /api/v1/quiz/sessions`.
3. Backend `list_sessions()` returns paginated session list.
4. User clicks `Open Summary`; frontend queries summary endpoint for selected session.
5. History page renders selected summary by topic.

### Backend files involved

- `backend/app/api/quiz.py`

### Frontend files involved

- `frontend/src/pages/ResultsPage.tsx`
- `frontend/src/pages/HistoryPage.tsx`
- `frontend/src/components/NavTabs.tsx`
- `frontend/src/App.tsx`

## 6) App Lifecycle and Health

1. FastAPI startup (`backend/app/main.py`) runs `create_db_and_tables()` via lifespan.
2. `GET /health` checks Ollama reachability/model in `backend/app/llm/ollama.py`.
3. Frontend polls health every 20s in `App.tsx`.
4. `HealthBanner.tsx` shows:
   - backend unreachable state,
   - model unavailable warning,
   - healthy connected state.

## 7) Contract and Data Ownership Notes

- API contracts live in `backend/app/schemas/quiz.py` and are mirrored in `frontend/src/types/api.ts`.
- Frontend only displays user-safe question fields from `QuizQuestionPublic` (no answer leakage in create-session response).
- Persistent source of truth is SQLite models in `backend/app/db/models.py`.
- Frontend state in `App.tsx` is session-local UI state:
  - active view,
  - current session payload,
  - submitted answer map,
  - current question index.
