import { describe, expect, it } from 'vitest'
import { renderToStaticMarkup } from 'react-dom/server'
import { SetupPage } from './pages/SetupPage'

describe('Setup page', () => {
  it('renders setup form controls', () => {
    const html = renderToStaticMarkup(
      <SetupPage onStart={() => undefined} isStarting={false} error={null} />,
    )

    expect(html).toContain('Quiz Setup')
    expect(html).toContain('Start Quiz')
    expect(html).toContain('Number of Questions')
    expect(html).toContain('Question Type')
  })
})
