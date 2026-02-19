import { useMemo, useState } from 'react'
import type {
  CreateQuizSessionResponse,
  QuizQuestionPublic,
  SubmitAnswerRequest,
  SubmitAnswerResponse,
} from '../types/api'

type AnswerRecord = {
  request: SubmitAnswerRequest
  response: SubmitAnswerResponse
}

type QuizRunnerPageProps = {
  session: CreateQuizSessionResponse
  currentIndex: number
  answers: Record<string, AnswerRecord>
  isSubmitting: boolean
  submitError: string | null
  onSubmitAnswer: (question: QuizQuestionPublic, payload: SubmitAnswerRequest) => void
  onNext: () => void
  onFinish: () => void
}

function getQuestionLabel(index: number, total: number) {
  return `Question ${index + 1} of ${total}`
}

export function QuizRunnerPage({
  session,
  currentIndex,
  answers,
  isSubmitting,
  submitError,
  onSubmitAnswer,
  onNext,
  onFinish,
}: QuizRunnerPageProps) {
  const question = session.questions[currentIndex]
  const total = session.questions.length
  const answerRecord = answers[question.id]
  const [selectedOption, setSelectedOption] = useState<number | null>(null)
  const [shortAnswer, setShortAnswer] = useState('')

  const questionLabel = useMemo(() => getQuestionLabel(currentIndex, total), [currentIndex, total])

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (question.type === 'mcq') {
      if (selectedOption === null) {
        return
      }
      onSubmitAnswer(question, { option_index: selectedOption })
      return
    }

    if (!shortAnswer.trim()) {
      return
    }
    onSubmitAnswer(question, { answer: shortAnswer })
  }

  const isLast = currentIndex === total - 1

  return (
    <section className="panel" data-testid="quiz-page">
      <h2>Quiz Runner</h2>
      <p className="question-counter">{questionLabel}</p>
      <article className="question-card">
        <h3>{question.prompt}</h3>
        <p className="muted">
          Type: <strong>{question.type}</strong> | Difficulty: <strong>{question.difficulty}</strong>
        </p>
        <form onSubmit={handleSubmit}>
          {question.type === 'mcq' ? (
            <div className="option-list">
              {question.options?.map((option, index) => (
                <label key={option} className="option-row">
                  <input
                    type="radio"
                    name={`question-${question.id}`}
                    checked={selectedOption === index}
                    onChange={() => setSelectedOption(index)}
                    disabled={Boolean(answerRecord)}
                  />
                  <span>{option}</span>
                </label>
              ))}
            </div>
          ) : (
            <label>
              Your Answer
              <textarea
                value={shortAnswer}
                onChange={(event) => setShortAnswer(event.target.value)}
                rows={4}
                placeholder="Type your short answer"
                disabled={Boolean(answerRecord)}
              />
            </label>
          )}

          <button type="submit" disabled={Boolean(answerRecord) || isSubmitting}>
            {isSubmitting ? 'Submitting...' : 'Submit Answer'}
          </button>
        </form>
      </article>

      {submitError ? <p className="error-text">{submitError}</p> : null}

      {answerRecord ? (
        <section className={`feedback ${answerRecord.response.is_correct ? 'correct' : 'incorrect'}`}>
          <h4>{answerRecord.response.is_correct ? 'Correct' : 'Incorrect'}</h4>
          <p>
            <strong>Correct answer:</strong> {answerRecord.response.correct_answer}
          </p>
          <p>
            <strong>Explanation:</strong> {answerRecord.response.explanation}
          </p>
          {answerRecord.response.why_others_wrong.length > 0 ? (
            <ul>
              {answerRecord.response.why_others_wrong.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          ) : null}
          <p>
            <strong>Normalized answer:</strong> {answerRecord.response.normalized_user_answer}
          </p>
        </section>
      ) : null}

      <div className="runner-actions">
        {isLast ? (
          <button type="button" onClick={onFinish} disabled={!answerRecord}>
            Finish Quiz
          </button>
        ) : (
          <button type="button" onClick={onNext} disabled={!answerRecord}>
            Next Question
          </button>
        )}
      </div>
    </section>
  )
}
