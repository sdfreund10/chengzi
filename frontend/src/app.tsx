import { useEffect, useState } from 'preact/hooks'
import './app.css'

type Health = {
  status: string
  service: string
  database: string
}

export function App() {
  const [health, setHealth] = useState<Health | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  async function load() {
    setError(null)
    try {
      const healthRes = await fetch('/api/health/')

      if (!healthRes.ok) {
        throw new Error('API request failed')
      }

      setHealth(await healthRes.json())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reach API')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [])

  return (
    <main class="app">
      <header>
        <p class="eyebrow">chengzi</p>
        <h1>Django + Postgres + Preact</h1>
        <p class="lede">
          A minimal full-stack scaffold. The UI talks to Django REST over{' '}
          <code>/api</code>, proxied by Vite in development.
        </p>
      </header>

      <section class="panel">
        <h2>API health</h2>
        {loading && <p>Checking…</p>}
        {error && <p class="error">{error}</p>}
        {health && !error && (
          <dl>
            <div>
              <dt>status</dt>
              <dd>{health.status}</dd>
            </div>
            <div>
              <dt>service</dt>
              <dd>{health.service}</dd>
            </div>
            <div>
              <dt>database</dt>
              <dd>{health.database}</dd>
            </div>
          </dl>
        )}
      </section>
    </main>
  )
}
