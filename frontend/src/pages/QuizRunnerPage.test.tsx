import { describe, expect, it } from 'vitest'
import { renderToStaticMarkup } from 'react-dom/server'
import { QuizRunnerPage } from './QuizRunnerPage'
import type { CreateQuizSessionResponse } from '../types/api'

const baseSession: CreateQuizSessionResponse = {
  session_id: 's1',
  created_at: '2026-02-19T00:00:00Z',
  config: {
    topics: ['Machine Learning technical concepts'],
    difficulty: 'easy',
    question_type: 'mixed',
    num_questions: 2,
  },
  questions: [
    {
      id: 'q1',
      order_index: 1,
      type: 'mcq',
      topic_tags: ['Machine Learning technical concepts'],
      difficulty: 'easy',
      prompt: 'Pick one',
      options: ['A', 'B', 'C', 'D'],
    },
    {
      id: 'q2',
      order_index: 2,
      type: 'short-answer',
      topic_tags: ['Machine Learning technical concepts'],
      difficulty: 'easy',
      prompt: 'Explain overfitting',
      options: null,
    },
  ],
}

describe('QuizRunnerPage', () => {
  it('renders MCQ question UI', () => {
    const html = renderToStaticMarkup(
      <QuizRunnerPage
        session={baseSession}
        currentIndex={0}
        answers={{}}
        isSubmitting={false}
        submitError={null}
        onSubmitAnswer={() => undefined}
        onNext={() => undefined}
        onFinish={() => undefined}
      />,
    )

    expect(html).toContain('Pick one')
    expect(html).toContain('Submit Answer')
    expect(html).toContain('A')
    expect(html).toContain('B')
  })

  it('renders short-answer question UI', () => {
    const html = renderToStaticMarkup(
      <QuizRunnerPage
        session={baseSession}
        currentIndex={1}
        answers={{}}
        isSubmitting={false}
        submitError={null}
        onSubmitAnswer={() => undefined}
        onNext={() => undefined}
        onFinish={() => undefined}
      />,
    )

    expect(html).toContain('Explain overfitting')
    expect(html).toContain('Your Answer')
  })
})
