import { useEffect, useState } from 'preact/hooks'
import {
  ApiError,
  fetchCategories,
  logout,
  type AuthUser,
  type Category,
} from './api'

type DecksProps = {
  user: AuthUser
  onSignedOut: () => void
  onSelectCategory: (category: Category) => void
}

export function Decks({ user, onSignedOut, onSelectCategory }: DecksProps) {
  const [categories, setCategories] = useState<Category[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [signingOut, setSigningOut] = useState(false)

  useEffect(() => {
    let cancelled = false

    async function load() {
      try {
        const rows = await fetchCategories()
        if (!cancelled) {
          setCategories(rows)
          setError(null)
        }
      } catch (err) {
        if (cancelled) return
        if (err instanceof ApiError && err.status === 401) {
          onSignedOut()
          return
        }
        setError('Could not load decks. Try again.')
        setCategories([])
      }
    }

    void load()
    return () => {
      cancelled = true
    }
    // Load once on mount; onSignedOut is stable enough for this shell.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function onSignOut() {
    setError(null)
    setSigningOut(true)
    try {
      await logout()
      onSignedOut()
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        onSignedOut()
        return
      }
      setError('Could not sign out. Try again.')
    } finally {
      setSigningOut(false)
    }
  }

  return (
    <main class="app">
      <header class="app-header">
        <div>
          <p class="eyebrow">juzi</p>
          <h1>Choose a deck</h1>
          <p class="lede">Pick a topic, then set difficulty.</p>
        </div>
        <div class="session">
          <p class="session-email">{user.email}</p>
          <button
            type="button"
            class="btn ghost"
            onClick={onSignOut}
            disabled={signingOut}
          >
            {signingOut ? 'Signing out…' : 'Sign out'}
          </button>
        </div>
      </header>

      {error && (
        <p class="error" role="alert" aria-live="polite">
          {error}
        </p>
      )}

      {categories === null ? (
        <p class="muted">Loading decks…</p>
      ) : categories.length === 0 ? (
        <section class="panel">
          <p class="muted">No decks yet. Seed vocabulary to get started.</p>
        </section>
      ) : (
        <section class="list" aria-label="Decks">
          {categories.map((category) => (
            <button
              key={category.id}
              type="button"
              class="row"
              onClick={() => onSelectCategory(category)}
            >
              <span class="row-body">
                <span class="row-title">{category.name}</span>
              </span>
            </button>
          ))}
        </section>
      )}
    </main>
  )
}
