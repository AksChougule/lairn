import { expect, test } from '@playwright/test'

const sessionResponse = {
  session_id: 'session-e2e-1',
  created_at: '2026-02-19T00:00:00Z',
  config: {
    topics: ['Machine Learning'],
    difficulty: 'medium',
    question_type: 'mcq',
    num_questions: 1,
  },
  questions: [
    {
      id: 'q1',
      order_index: 1,
      type: 'mcq',
      topic_tags: ['Machine Learning'],
      difficulty: 'medium',
      prompt: 'What is overfitting?',
      options: ['Good generalization', 'Memorization', 'Deployment', 'Logging'],
    },
  ],
}

test.beforeEach(async ({ page }) => {
  await page.route('**/health', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ status: 'ok', ollama: { reachable: true, model: 'qwen3:1.7b' } }),
    })
  })

  await page.route('**/api/v1/quiz/sessions?*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        limit: 20,
        offset: 0,
        items: [
          {
            session_id: 'session-e2e-1',
            created_at: '2026-02-19T00:00:00Z',
            completed_at: '2026-02-19T00:05:00Z',
            score: { correct: 1, total: 1 },
            config: {
              topics: ['Machine Learning'],
              difficulty: 'medium',
              question_type: 'mcq',
              num_questions: 1,
            },
          },
        ],
      }),
    })
  })

  await page.route('**/api/v1/quiz/sessions/session-e2e-1/summary', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        session_id: 'session-e2e-1',
        score: { correct: 1, total: 1 },
        by_topic: [{ topic: 'Machine Learning', correct: 1, total: 1 }],
        created_at: '2026-02-19T00:00:00Z',
        completed_at: '2026-02-19T00:05:00Z',
      }),
    })
  })

  await page.route('**/api/v1/quiz/sessions', async (route) => {
    if (route.request().method() !== 'POST') {
      return route.fallback()
    }
    await route.fulfill({
      status: 201,
      contentType: 'application/json',
      body: JSON.stringify(sessionResponse),
    })
  })

  await page.route('**/api/v1/quiz/sessions/session-e2e-1/questions/q1/answer', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        is_correct: true,
        correct_answer: 'Memorization',
        explanation: 'Overfitting memorizes training patterns.',
        why_others_wrong: ['Not related 1', 'Not related 2', 'Not related 3'],
        normalized_user_answer: 'memorization',
      }),
    })
  })
})

test('happy path start -> answer -> feedback -> results', async ({ page }) => {
  await page.goto('/')

  await page.fill('input[type="number"]', '1')
  await page.click('button:has-text("Start Quiz")')

  await expect(page.getByTestId('quiz-page')).toBeVisible()
  await page.check('input[type="radio"]').catch(async () => {
    await page.click('label:has-text("Memorization") input[type="radio"]')
  })
  await page.click('button:has-text("Submit Answer")')
  await expect(page.getByText('Correct answer:')).toBeVisible()

  await page.click('button:has-text("Finish Quiz")')
  await expect(page.getByTestId('results-page')).toBeVisible()
  await expect(page.getByText('Score')).toBeVisible()
})

test('history page lists sessions', async ({ page }) => {
  await page.goto('/')
  await page.click('button:has-text("History")')

  await expect(page.getByTestId('history-page')).toBeVisible()
  await expect(page.getByText('session-')).toBeVisible()

  await page.click('button:has-text("Open Summary")')
  await expect(page.getByText('Session Summary')).toBeVisible()
  await expect(page.getByText('Machine Learning: 1/1')).toBeVisible()
})
