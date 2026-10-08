import { useState } from 'preact/hooks'
import { ApiError, logout, type AuthUser } from './api'

type DecksProps = {
  user: AuthUser
  onSignedOut: () => void
}

export function Decks({ user, onSignedOut }: DecksProps) {
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

  return (
    <main class="app">
      <header class="app-header">
        <div>
          <p class="eyebrow">juzi</p>
          <h1>Decks</h1>
          <p class="lede">Pick a deck to practice. Deck list arrives with the next slice.</p>
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
          {error && (
            <p class="error session-error" role="alert" aria-live="polite">
              {error}
            </p>
          )}
        </div>
      </header>

      <section class="panel">
        <h2>Coming soon</h2>
        <p class="muted">Your decks will show up here once the deck-picker API lands.</p>
      </section>
    </main>
  )
}
