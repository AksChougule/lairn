import type { CreateQuizSessionResponse, SessionSummaryResponse, SubmitAnswerRequest, SubmitAnswerResponse } from '../types/api'
import { getTopicLabel } from '../constants/topics'

type AnswerRecord = {
  request: SubmitAnswerRequest
  response: SubmitAnswerResponse
}

type ResultsPageProps = {
  summary: SessionSummaryResponse | null
  session: CreateQuizSessionResponse | null
  answers: Record<string, AnswerRecord>
  isLoading: boolean
  error: string | null
  onRestart: () => void
}

function formatDate(value: string | null) {
  if (!value) {
    return 'Not completed'
  }
  return new Date(value).toLocaleString()
}

export function ResultsPage({ summary, session, answers, isLoading, error, onRestart }: ResultsPageProps) {
  if (isLoading) {
    return (
      <section className="panel" data-testid="results-page">
        <h2>Results</h2>
        <p>Loading summary...</p>
      </section>
    )
  }

  if (error) {
    return (
      <section className="panel" data-testid="results-page">
        <h2>Results</h2>
        <p className="error-text">{error}</p>
      </section>
    )
  }

  if (!summary) {
    return (
      <section className="panel" data-testid="results-page">
        <h2>Results</h2>
        <p className="muted">Complete a quiz to see summary and review.</p>
      </section>
    )
  }

  return (
    <section className="panel" data-testid="results-page">
      <h2>Results</h2>
      <div className="stat-grid">
        <div className="stat-card">
          <p>Score</p>
          <strong>
            {summary.score.correct}/{summary.score.total}
          </strong>
        </div>
        <div className="stat-card">
          <p>Created</p>
          <strong>{formatDate(summary.created_at)}</strong>
        </div>
        <div className="stat-card">
          <p>Completed</p>
          <strong>{formatDate(summary.completed_at)}</strong>
        </div>
      </div>

      <h3>By Topic</h3>
      <ul className="topic-summary">
        {summary.by_topic.map((item) => (
          <li key={item.topic}>
            <span>{getTopicLabel(item.topic)}</span>
            <strong>
              {item.correct}/{item.total}
            </strong>
          </li>
        ))}
      </ul>

      {session ? (
        <>
          <h3>Review</h3>
          <div className="review-list">
            {session.questions.map((question) => {
              const answer = answers[question.id]
              return (
                <article key={question.id} className="review-item">
                  <h4>
                    #{question.order_index} {question.prompt}
                  </h4>
                  <p>
                    <strong>Your input:</strong>{' '}
                    {typeof answer?.request.option_index === 'number'
                      ? `Option ${answer.request.option_index + 1}`
                      : answer?.request.answer || 'Not answered'}
                  </p>
                  <p>
                    <strong>Correct answer:</strong> {answer?.response.correct_answer ?? 'N/A'}
                  </p>
                  <p>
                    <strong>Explanation:</strong> {answer?.response.explanation ?? 'N/A'}
                  </p>
                </article>
              )
            })}
          </div>
          <div className="results-actions">
            <button type="button" onClick={onRestart}>
              Restart Quiz
            </button>
          </div>
        </>
      ) : null}
    </section>
  )
}
