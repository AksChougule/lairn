export type AppView = 'setup' | 'quiz' | 'results' | 'history'

type NavTabsProps = {
  activeView: AppView
  onChange: (view: AppView) => void
  canOpenQuiz: boolean
  canOpenResults: boolean
}

const tabs: Array<{ id: AppView; label: string }> = [
  { id: 'setup', label: 'Setup' },
  { id: 'quiz', label: 'Quiz Runner' },
  { id: 'results', label: 'Results' },
  { id: 'history', label: 'History' },
]

export function NavTabs({ activeView, onChange, canOpenQuiz, canOpenResults }: NavTabsProps) {
  return (
    <nav className="tabs" aria-label="Primary">
      {tabs.map((tab) => {
        const disabled = (tab.id === 'quiz' && !canOpenQuiz) || (tab.id === 'results' && !canOpenResults)
        return (
          <button
            key={tab.id}
            type="button"
            className={`tab ${activeView === tab.id ? 'active' : ''}`}
            disabled={disabled}
            onClick={() => onChange(tab.id)}
          >
            {tab.label}
          </button>
        )
      })}
    </nav>
  )
}
