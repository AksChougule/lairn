import { describe, expect, it } from 'vitest'
import { renderToStaticMarkup } from 'react-dom/server'
import { ResultsPage } from './ResultsPage'

describe('ResultsPage', () => {
  it('renders summary and review data', () => {
    const html = renderToStaticMarkup(
      <ResultsPage
        isLoading={false}
        error={null}
        onRestart={() => undefined}
        summary={{
          session_id: 's1',
          score: { correct: 1, total: 2 },
          by_topic: [{ topic: 'Machine Learning', correct: 1, total: 2 }],
          created_at: '2026-02-19T00:00:00Z',
          completed_at: '2026-02-19T00:03:00Z',
        }}
        session={{
          session_id: 's1',
          created_at: '2026-02-19T00:00:00Z',
          config: {
            topics: ['Machine Learning'],
            difficulty: 'easy',
            question_type: 'mixed',
            num_questions: 1,
          },
          questions: [
            {
              id: 'q1',
              order_index: 1,
              type: 'mcq',
              topic_tags: ['Machine Learning'],
              difficulty: 'easy',
              prompt: 'Pick one',
              options: ['A', 'B', 'C', 'D'],
            },
          ],
        }}
        answers={{
          q1: {
            request: { option_index: 1 },
            response: {
              is_correct: true,
              correct_answer: 'B',
              explanation: 'Because B is right.',
              why_others_wrong: [],
              normalized_user_answer: 'b',
            },
          },
        }}
      />,
    )

    expect(html).toContain('Results')
    expect(html).toContain('Machine Learning')
    expect(html).toContain('Because B is right.')
    expect(html).toContain('Restart Quiz')
  })
})
