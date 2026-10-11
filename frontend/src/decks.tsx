import { useState } from 'preact/hooks'
import { ApiError, logout, type AuthUser, type Category } from './api'

type DecksProps = {
  user: AuthUser
  categories: Category[] | null
  categoriesError: string | null
  onSignedOut: () => void
  onSelectCategory: (category: Category) => void
}

function wordCount(category: Category): number {
  return (
    category.beginner_count +
    category.intermediate_count +
    category.advanced_count
  )
}

export function Decks({
  user,
  categories,
  categoriesError,
  onSignedOut,
  onSelectCategory,
}: DecksProps) {
  const [error, setError] = useState<string | null>(null)
  const [signingOut, setSigningOut] = useState(false)

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

  const banner = error ?? categoriesError

  return (
    <main class="app">
      <h1 class="title">Choose a deck</h1>

      {banner && (
        <p class="error" role="alert" aria-live="polite">
          {banner}
        </p>
      )}

      {categories === null ? (
        <p class="subtitle">Loading decks…</p>
      ) : categories.length === 0 ? (
        <section class="panel">
          <p>No decks yet. Seed vocabulary to get started.</p>
        </section>
      ) : (
        <section class="list" aria-label="Decks">
          {categories.map((category) => {
            const total = wordCount(category)
            return (
              <button
                key={category.id}
                type="button"
                class="row"
                onClick={() => onSelectCategory(category)}
              >
                <span class="g">
                  <b>{category.name}</b>
                  <span class="s">
                    {total === 1 ? '1 word' : `${total} words`}
                  </span>
                </span>
              </button>
            )
          })}
        </section>
      )}

      <footer class="session-footer">
        <span class="session-email">{user.email}</span>
        <button
          type="button"
          class="link-btn"
          onClick={onSignOut}
          disabled={signingOut}
        >
          {signingOut ? 'Signing out…' : 'Sign out'}
        </button>
      </footer>
    </main>
  )
}
