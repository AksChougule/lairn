import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getSessionSummary, listSessions } from '../api/quiz'

export function HistoryPage() {
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null)

  const sessionsQuery = useQuery({
    queryKey: ['history-sessions'],
    queryFn: () => listSessions(20, 0),
  })

  const summaryQuery = useQuery({
    queryKey: ['history-summary', selectedSessionId],
    queryFn: () => getSessionSummary(selectedSessionId as string),
    enabled: selectedSessionId !== null,
  })

  return (
    <section className="panel" data-testid="history-page">
      <h2>History</h2>

      {sessionsQuery.isLoading ? <p>Loading sessions...</p> : null}
      {sessionsQuery.isError ? <p className="error-text">Could not load session history.</p> : null}

      <div className="history-table" role="table" aria-label="Session history">
        {sessionsQuery.data?.items.map((session) => (
          <div className="history-row" key={session.session_id}>
            <div>
              <strong>{session.session_id.slice(0, 8)}</strong>
              <p className="muted">{new Date(session.created_at).toLocaleString()}</p>
            </div>
            <div>
              <span>
                Score: {session.score.correct}/{session.score.total}
              </span>
            </div>
            <button type="button" onClick={() => setSelectedSessionId(session.session_id)}>
              Open Summary
            </button>
          </div>
        ))}
      </div>

      {summaryQuery.isLoading ? <p>Loading summary...</p> : null}
      {summaryQuery.isError ? <p className="error-text">Could not load selected summary.</p> : null}

      {summaryQuery.data ? (
        <article className="history-summary">
          <h3>Session Summary</h3>
          <p>
            Score: {summaryQuery.data.score.correct}/{summaryQuery.data.score.total}
          </p>
          <ul>
            {summaryQuery.data.by_topic.map((topic) => (
              <li key={topic.topic}>
                {topic.topic}: {topic.correct}/{topic.total}
              </li>
            ))}
          </ul>
        </article>
      ) : null}
    </section>
  )
}
