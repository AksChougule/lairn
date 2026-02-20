# PROJECT_STRUCTURE

This guide explains what the major files/directories do, why they exist, and how they interact.

## Root

- `README.md`
  - Purpose: onboarding and run/test instructions.
  - Type: infrastructure/documentation.
- `lairn_spec_0.1.md`
  - Purpose: product/API specification baseline.
  - Type: product contract/documentation.
- `backend/`
  - Purpose: API server, domain logic, persistence, LLM integration.
  - Type: backend application.
- `frontend/`
  - Purpose: user interface, client-side state, API consumption.
  - Type: frontend application.

## Backend

### `backend/app/main.py`

- What: FastAPI app entrypoint.
- Why: central app bootstrap for routing and startup lifecycle.
- Interactions:
  - includes quiz router from `app/api/quiz.py`,
  - initializes DB schema on startup (`create_db_and_tables()`),
  - serves `/health` using Ollama health check.
- Classification: infrastructure/composition root.

### `backend/app/api/`

- What: HTTP route layer.
- Why: expose domain operations as REST endpoints.
- Main file:
  - `backend/app/api/quiz.py` handles session creation, answer submission, summary, and history list.
- Interactions:
  - validates request/response through `app/schemas/quiz.py`,
  - calls domain services in `app/quiz/`,
  - reads/writes models via DB session.
- Classification: API adapter layer.

### `backend/app/quiz/`

- What: quiz domain logic.
- Why: keep generation/evaluation logic separate from HTTP handlers.
- Files:
  - `backend/app/quiz/generator.py`
    - LLM question generation prompt + parsing.
    - fallback question bank.
    - prompt deduplication and targeted duplicate regeneration.
  - `backend/app/quiz/evaluator.py`
    - short-answer normalization,
    - deterministic match checks,
    - LLM judge integration,
    - deterministic fallback explanation.
- Interactions:
  - uses `app/llm/ollama.py` for model calls,
  - uses schema enums (`Topic`, `Difficulty`, `QuestionType`).
- Classification: domain logic.

### `backend/app/llm/`

- What: LLM integration layer.
- Why: isolate Ollama-specific transport/parsing concerns.
- Main file:
  - `backend/app/llm/ollama.py`
    - checks model availability,
    - sends generate requests,
    - parses/validates JSON,
    - retries on parse/network/schema failures.
- Interactions:
  - used by generator and evaluator modules.
- Classification: infrastructure adapter.

### `backend/app/db/`

- What: persistence layer.
- Why: define data model and DB engine/session setup in one place.
- Files:
  - `backend/app/db/models.py`
    - SQLModel tables: `QuizSession`, `QuizQuestion`, `QuizAnswer`.
  - `backend/app/db/session.py`
    - engine creation,
    - table creation helper,
    - `get_session()` dependency for FastAPI routes.
- Interactions:
  - routes persist and query these models directly.
- Classification: infrastructure/persistence.

### `backend/app/schemas/`

- What: API request/response schemas + enums.
- Why: enforce contract consistency and validation at API boundary.
- Main file:
  - `backend/app/schemas/quiz.py`
    - topic/difficulty/type enums,
    - request DTOs (create, submit),
    - response DTOs (session creation, answer result, summary, list).
- Interactions:
  - consumed by route handlers and mirrored in frontend TypeScript types.
- Classification: contract layer.

### `backend/app/tests/`

- What: backend test suite.
- Why: validate endpoint behavior and domain reliability.
- Key tests:
  - `test_quiz_sessions.py`: session creation/submission/summary/list flows.
  - `test_quiz_generation.py`: generation limits and duplicate prompt handling.
  - `test_short_answer_grading.py`: fallback behavior and JSON parse retry resilience.
- Classification: quality/verification.

### `backend/app/core/config.py`

- What: environment-driven settings.
- Why: centralize runtime config (`database_url`, `sqlite_path`, Ollama base/model/timeout).
- Interactions:
  - DB session setup,
  - Ollama client configuration.
- Classification: infrastructure/config.

## Frontend

### `frontend/src/pages/`

- What: top-level page views.
- Why: separate UI concerns by user workflow.
- Files:
  - `SetupPage.tsx`: create quiz form.
  - `QuizRunnerPage.tsx`: current question, answer submit, feedback, next/finish actions.
  - `ResultsPage.tsx`: score, by-topic summary, question review, restart action.
  - `HistoryPage.tsx`: list sessions and open historical summary.
- Interactions:
  - orchestrated by `App.tsx`,
  - call mutation/query callbacks passed from `App.tsx`.
- Classification: UI logic.

### `frontend/src/components/`

- What: reusable UI components.
- Why: avoid duplicating cross-page UI behavior.
- Files:
  - `NavTabs.tsx`: view switching controls.
  - `HealthBanner.tsx`: backend/Ollama health status messaging.
- Interactions:
  - mounted by `App.tsx`.
- Classification: UI infrastructure.

### `frontend/src/api/`

- What: HTTP client and endpoint wrappers.
- Why: keep network code centralized and typed.
- Files:
  - `client.ts`: axios instance.
  - `quiz.ts`: endpoint functions (`getHealth`, `createQuizSession`, `submitAnswer`, `getSessionSummary`, `listSessions`).
- Interactions:
  - used by React Query hooks in `App.tsx` and pages.
- Classification: frontend infrastructure adapter.

### Routing setup

- Current pattern: view-state routing in `frontend/src/App.tsx` (not React Router).
- `activeView` controls which page component renders (`setup`, `quiz`, `results`, `history`).
- `NavTabs.tsx` updates this state.
- Classification: UI orchestration/stateful navigation.

### State management

- Server state: TanStack React Query in `App.tsx` and `HistoryPage.tsx`.
- Client/session state: React `useState` in `App.tsx`:
  - current session payload,
  - answer map,
  - current question index,
  - local error flags/view state.
- Shared static mapping: `frontend/src/constants/topics.ts`.
- Types: `frontend/src/types/api.ts` mirrors backend schema contract.
- Classification: mixed UI + data state management.

### Test setup

- Unit/component tests:
  - `frontend/src/**/*.test.tsx` via Vitest.
  - setup file: `frontend/src/setupTests.ts`.
  - helper wrapper: `frontend/src/test/test-utils.tsx`.
- E2E tests:
  - `frontend/tests/e2e/app.spec.ts` with Playwright.
  - config: `frontend/playwright.config.ts` (starts Vite dev server).
- Classification: quality/verification.

### Other key frontend infrastructure

- `frontend/src/main.tsx`
  - app bootstrap + `QueryClientProvider`.
- `frontend/vite.config.ts`
  - Vite config, React plugin,
  - dev proxy to backend for `/api` and `/health`.
- `frontend/src/constants/topics.ts`
  - centralized `{ value, label }` mapping where internal topic values differ from display labels.

## Layer Classification Summary

- Infrastructure:
  - backend app/bootstrap, DB setup, config, Ollama client, frontend API client, build/test configs.
- Domain logic:
  - question generation and dedup,
  - short-answer evaluation.
- UI logic:
  - page rendering, local view/session state, user interactions.
