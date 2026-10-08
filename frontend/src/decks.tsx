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
          <p class="brand">juzi</p>
          <h1>Choose a deck</h1>
          <p class="lede">Deck list arrives with the next slice.</p>
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

      <section class="list" aria-label="Decks">
        <div class="row">
          <span class="row-body">
            <span class="row-title">Coming soon</span>
            <span class="row-meta">Your decks will show up here once the deck-picker API lands.</span>
          </span>
          <span class="badge none">None due</span>
        </div>
      </section>

      <section class="theme-preview" aria-label="Theme preview">
        <div class="theme-preview-top">
          <span class="chip">Pinyin to English</span>
          <span class="muted">1 / 3</span>
        </div>
        <p class="prompt zh pinyin">túshūguǎn</p>
        <p class="hint">Tap anywhere to reveal</p>
        <div class="zones" aria-hidden="true">
          <div class="zone hard">
            Hard
            <small>back soon</small>
          </div>
          <div class="zone easy">
            Easy
            <small>later</small>
          </div>
        </div>
      </section>
    </main>
  )
}
