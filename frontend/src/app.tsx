import { useEffect, useState } from 'preact/hooks'
import './app.css'
import { ApiError, fetchMe, type AuthUser } from './api'
import { Decks } from './decks'
import { Login } from './login'

type Screen = 'loading' | 'login' | 'decks'

export function App() {
  const [screen, setScreen] = useState<Screen>('loading')
  const [user, setUser] = useState<AuthUser | null>(null)
  const [bootError, setBootError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function boot() {
      try {
        const me = await fetchMe()
        if (cancelled) return
        if (me.authenticated) {
          setUser(me)
          setScreen('decks')
        } else {
          setUser(null)
          setScreen('login')
        }
      } catch (err) {
        if (cancelled) return
        if (err instanceof ApiError && err.status === 401) {
          setUser(null)
          setScreen('login')
          return
        }
        setBootError(err instanceof Error ? err.message : 'Failed to reach API')
        setScreen('login')
      }
    }

    void boot()
    return () => {
      cancelled = true
    }
  }, [])

  if (screen === 'loading') {
    return (
      <main class="app">
        <p class="muted">Loading…</p>
      </main>
    )
  }

  if (screen === 'login' || !user) {
    return (
      <Login
        bootError={bootError}
        onSuccess={(next) => {
          setBootError(null)
          setUser(next)
          setScreen('decks')
        }}
      />
    )
  }

  return (
    <Decks
      user={user}
      onSignedOut={() => {
        setUser(null)
        setScreen('login')
      }}
    />
  )
}
