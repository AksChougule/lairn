import { useMemo, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { createQuizSession, getHealth, getSessionSummary, submitAnswer } from './api/quiz'
import { HealthBanner } from './components/HealthBanner'
import { NavTabs, type AppView } from './components/NavTabs'
import { HistoryPage } from './pages/HistoryPage'
import { QuizRunnerPage } from './pages/QuizRunnerPage'
import { ResultsPage } from './pages/ResultsPage'
import { SetupPage } from './pages/SetupPage'
import type {
  CreateQuizSessionRequest,
  CreateQuizSessionResponse,
  QuizQuestionPublic,
  SubmitAnswerRequest,
  SubmitAnswerResponse,
} from './types/api'

type AnswerRecord = {
  request: SubmitAnswerRequest
  response: SubmitAnswerResponse
}

function App() {
  const [activeView, setActiveView] = useState<AppView>('setup')
  const [session, setSession] = useState<CreateQuizSessionResponse | null>(null)
  const [answers, setAnswers] = useState<Record<string, AnswerRecord>>({})
  const [currentIndex, setCurrentIndex] = useState(0)
  const [summaryError, setSummaryError] = useState<string | null>(null)

  const healthQuery = useQuery({
    queryKey: ['health'],
    queryFn: getHealth,
    refetchInterval: 20000,
  })

  const createSessionMutation = useMutation({
    mutationFn: (payload: CreateQuizSessionRequest) => createQuizSession(payload),
    onSuccess: (data) => {
      setSession(data)
      setAnswers({})
      setCurrentIndex(0)
      setSummaryError(null)
      setActiveView('quiz')
    },
  })

  const submitMutation = useMutation({
    mutationFn: ({ question, payload }: { question: QuizQuestionPublic; payload: SubmitAnswerRequest }) => {
      if (!session) {
        throw new Error('No session available')
      }
      return submitAnswer(session.session_id, question.id, payload)
    },
    onSuccess: (response, variables) => {
      setAnswers((current) => ({
        ...current,
        [variables.question.id]: { request: variables.payload, response },
      }))
    },
  })

  const summaryQuery = useQuery({
    queryKey: ['session-summary', session?.session_id],
    queryFn: () => getSessionSummary(session?.session_id as string),
    enabled: activeView === 'results' && session !== null,
  })

  function handleStartQuiz(payload: CreateQuizSessionRequest) {
    createSessionMutation.mutate(payload)
  }

  function handleSubmitAnswer(question: QuizQuestionPublic, payload: SubmitAnswerRequest) {
    submitMutation.mutate({ question, payload })
  }

  function handleNext() {
    if (!session) {
      return
    }
    setCurrentIndex((value) => Math.min(value + 1, session.questions.length - 1))
  }

  function handleFinish() {
    if (!session) {
      return
    }
    setSummaryError(null)
    setActiveView('results')
  }

  function handleRestart() {
    setSession(null)
    setAnswers({})
    setCurrentIndex(0)
    setSummaryError(null)
    createSessionMutation.reset()
    submitMutation.reset()
    setActiveView('setup')
  }

  const canOpenQuiz = session !== null
  const canOpenResults = session !== null

  const setupError = createSessionMutation.isError
    ? 'Could not create quiz session. Verify backend health and input values.'
    : null

  const submitError = submitMutation.isError ? 'Could not submit answer. Try again.' : null

  const resolvedSummaryError = useMemo(() => {
    if (summaryError) {
      return summaryError
    }
    if (summaryQuery.isError) {
      return 'Could not load session summary.'
    }
    return null
  }, [summaryError, summaryQuery.isError])

  return (
    <div className="app-shell">
      <header>
        <h1>Lairn</h1>
        <p>Local AI quiz trainer for ML, GenAI, and MLOps topics.</p>
      </header>

      <HealthBanner health={healthQuery.data} isError={healthQuery.isError} />

      <NavTabs
        activeView={activeView}
        onChange={setActiveView}
        canOpenQuiz={canOpenQuiz}
        canOpenResults={canOpenResults}
      />

      <main>
        {activeView === 'setup' ? (
          <SetupPage
            onStart={handleStartQuiz}
            isStarting={createSessionMutation.isPending}
            error={setupError}
          />
        ) : null}

        {activeView === 'quiz' && session ? (
          <QuizRunnerPage
            key={session.questions[currentIndex]?.id}
            session={session}
            currentIndex={currentIndex}
            answers={answers}
            isSubmitting={submitMutation.isPending}
            submitError={submitError}
            onSubmitAnswer={handleSubmitAnswer}
            onNext={handleNext}
            onFinish={handleFinish}
          />
        ) : null}

        {activeView === 'results' ? (
          <ResultsPage
            summary={summaryQuery.data ?? null}
            session={session}
            answers={answers}
            isLoading={summaryQuery.isLoading}
            error={resolvedSummaryError}
            onRestart={handleRestart}
          />
        ) : null}

        {activeView === 'history' ? <HistoryPage /> : null}
      </main>
    </div>
  )
}

export default App
