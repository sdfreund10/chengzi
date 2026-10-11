import { useEffect, useState } from 'preact/hooks'
import {
  ApiError,
  createSession,
  type Category,
  type Difficulty,
  type StudySession,
} from './api'

type BuildingProps = {
  category: Category
  difficulties: Difficulty[]
  onReady: (session: StudySession) => void
  onCancel: () => void
}

export function Building({
  category,
  difficulties,
  onReady,
  onCancel,
}: BuildingProps) {
  const [error, setError] = useState<string | null>(null)

  const difficultyKey = difficulties.join(',')

  useEffect(() => {
    let cancelled = false

    async function build() {
      try {
        const session = await createSession(category.id, difficulties)
        if (!cancelled) {
          onReady(session)
        }
      } catch (err) {
        if (cancelled) return
        const message =
          err instanceof ApiError && err.message
            ? err.message
            : 'Could not build deck. Try again.'
        setError(message)
      }
    }

    void build()
    return () => {
      cancelled = true
    }
    // Intentionally keyed on category + difficulty selection only.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [category.id, difficultyKey])

  return (
    <main class="app">
      <header>
        <p class="eyebrow">juzi</p>
        <h1>Building deck</h1>
        <p class="lede">{category.name}</p>
      </header>

      {error ? (
        <section class="panel">
          <p class="error" role="alert" aria-live="polite">
            {error}
          </p>
          <button type="button" class="btn ghost" onClick={onCancel}>
            Back
          </button>
        </section>
      ) : (
        <p class="building-status" aria-live="polite">
          Gathering cards…
        </p>
      )}
    </main>
  )
}
