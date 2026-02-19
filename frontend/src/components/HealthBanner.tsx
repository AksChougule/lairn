import type { HealthResponse } from '../types/api'

type HealthBannerProps = {
  health: HealthResponse | undefined
  isError: boolean
}

export function HealthBanner({ health, isError }: HealthBannerProps) {
  if (isError) {
    return (
      <div className="banner banner-error" role="alert">
        Backend is unreachable. Start backend at http://localhost:8000 and refresh.
      </div>
    )
  }

  if (!health) {
    return null
  }

  if (!health.ollama.reachable) {
    return (
      <div className="banner banner-warn" role="alert">
        Ollama model <strong>{health.ollama.model}</strong> is unavailable. Run <code>ollama pull {health.ollama.model}</code>.
      </div>
    )
  }

  return (
    <div className="banner banner-ok" role="status">
      Ollama connected: <strong>{health.ollama.model}</strong>
    </div>
  )
}
