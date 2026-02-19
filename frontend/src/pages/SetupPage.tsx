import { useState } from 'react'
import type { CreateQuizSessionRequest, Difficulty, QuestionType, Topic } from '../types/api'

type SetupPageProps = {
  onStart: (payload: CreateQuizSessionRequest) => void
  isStarting: boolean
  error: string | null
}

const TOPICS: Topic[] = [
  'Machine Learning',
  'Deep Learning',
  'Statistics',
  'Generative AI',
  'MLOps',
  'Agentic AI',
]

const DIFFICULTIES: Difficulty[] = ['easy', 'medium', 'hard']
const QUESTION_TYPES: QuestionType[] = ['mcq', 'short-answer', 'mixed']

export function SetupPage({ onStart, isStarting, error }: SetupPageProps) {
  const [selectedTopics, setSelectedTopics] = useState<Topic[]>(['Machine Learning'])
  const [difficulty, setDifficulty] = useState<Difficulty>('medium')
  const [questionType, setQuestionType] = useState<QuestionType>('mixed')
  const [numQuestions, setNumQuestions] = useState<number>(5)

  function toggleTopic(topic: Topic) {
    setSelectedTopics((current) => {
      if (current.includes(topic)) {
        return current.length > 1 ? current.filter((item) => item !== topic) : current
      }
      return [...current, topic]
    })
  }

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    onStart({
      topics: selectedTopics,
      difficulty,
      question_type: questionType,
      num_questions: numQuestions,
    })
  }

  return (
    <section className="panel" data-testid="setup-page">
      <h2>Quiz Setup</h2>
      <p className="muted">Pick topics, question style, and difficulty to create a new session.</p>
      <form className="form-grid" onSubmit={handleSubmit}>
        <fieldset>
          <legend>Topics</legend>
          <div className="topic-grid">
            {TOPICS.map((topic) => (
              <label key={topic} className="checkbox-card">
                <input
                  type="checkbox"
                  checked={selectedTopics.includes(topic)}
                  onChange={() => toggleTopic(topic)}
                />
                <span>{topic}</span>
              </label>
            ))}
          </div>
        </fieldset>

        <label>
          Difficulty
          <select value={difficulty} onChange={(event) => setDifficulty(event.target.value as Difficulty)}>
            {DIFFICULTIES.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>

        <label>
          Question Type
          <select value={questionType} onChange={(event) => setQuestionType(event.target.value as QuestionType)}>
            {QUESTION_TYPES.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>

        <label>
          Number of Questions
          <input
            type="number"
            min={1}
            max={50}
            value={numQuestions}
            onChange={(event) => setNumQuestions(Number(event.target.value))}
          />
        </label>

        <button type="submit" disabled={isStarting}>
          {isStarting ? 'Starting...' : 'Start Quiz'}
        </button>
      </form>
      {error ? <p className="error-text">{error}</p> : null}
    </section>
  )
}
