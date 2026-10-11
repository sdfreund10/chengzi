import { useEffect, useState } from 'preact/hooks'
import './app.css'
import {
  ApiError,
  fetchMe,
  type AuthUser,
  type Category,
  type Difficulty,
  type StudySession,
} from './api'
import { Building } from './building'
import { Decks } from './decks'
import { DifficultyStep } from './difficulty'
import { Login } from './login'
import { Study } from './study'

type Screen = 'loading' | 'login' | 'decks' | 'difficulty' | 'building' | 'study'

export function App() {
  const [screen, setScreen] = useState<Screen>('loading')
  const [user, setUser] = useState<AuthUser | null>(null)
  const [bootError, setBootError] = useState<string | null>(null)
  const [category, setCategory] = useState<Category | null>(null)
  const [difficulties, setDifficulties] = useState<Difficulty[]>([])
  const [session, setSession] = useState<StudySession | null>(null)

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

  function resetPicker() {
    setCategory(null)
    setDifficulties([])
    setSession(null)
    setScreen('decks')
  }

  function onSignedOut() {
    setUser(null)
    setCategory(null)
    setDifficulties([])
    setSession(null)
    setScreen('login')
  }

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

  if (screen === 'difficulty' && category) {
    return (
      <DifficultyStep
        category={category}
        onBack={() => {
          setDifficulties([])
          setScreen('decks')
        }}
        onContinue={(next) => {
          setDifficulties(next)
          setScreen('building')
        }}
      />
    )
  }

  if (screen === 'building' && category && difficulties.length > 0) {
    return (
      <Building
        category={category}
        difficulties={difficulties}
        onReady={(next) => {
          setSession(next)
          setScreen('study')
        }}
        onCancel={() => setScreen('difficulty')}
      />
    )
  }

  if (screen === 'study' && session) {
    return <Study session={session} onExit={resetPicker} />
  }

  return (
    <Decks
      user={user}
      onSignedOut={onSignedOut}
      onSelectCategory={(next) => {
        setCategory(next)
        setDifficulties([])
        setSession(null)
        setScreen('difficulty')
      }}
    />
  )
}
