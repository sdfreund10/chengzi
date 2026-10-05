import { useEffect, useState } from 'preact/hooks'
import './app.css'

type Health = {
  status: string
  service: string
  database: string
}

type Note = {
  id: number
  title: string
  body: string
  created_at: string
}

export function App() {
  const [health, setHealth] = useState<Health | null>(null)
  const [notes, setNotes] = useState<Note[]>([])
  const [title, setTitle] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  async function load() {
    setError(null)
    try {
      const [healthRes, notesRes] = await Promise.all([
        fetch('/api/health/'),
        fetch('/api/notes/'),
      ])

      if (!healthRes.ok || !notesRes.ok) {
        throw new Error('API request failed')
      }

      setHealth(await healthRes.json())
      setNotes(await notesRes.json())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reach API')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [])

  async function addNote(event: Event) {
    event.preventDefault()
    const trimmed = title.trim()
    if (!trimmed) return

    setError(null)
    try {
      const res = await fetch('/api/notes/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: trimmed, body: '' }),
      })
      if (!res.ok) throw new Error('Could not create note')
      setTitle('')
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not create note')
    }
  }

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

      <section class="panel">
        <h2>Notes</h2>
        <form onSubmit={addNote} class="note-form">
          <label>
            <span>Title</span>
            <input
              value={title}
              onInput={(e) => setTitle((e.target as HTMLInputElement).value)}
              placeholder="Write something Postgres will remember"
            />
          </label>
          <button type="submit">Add note</button>
        </form>

        {notes.length === 0 ? (
          <p class="muted">No notes yet.</p>
        ) : (
          <ul class="notes">
            {notes.map((note) => (
              <li key={note.id}>
                <strong>{note.title}</strong>
                <time dateTime={note.created_at}>
                  {new Date(note.created_at).toLocaleString()}
                </time>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  )
}
