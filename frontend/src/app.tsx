import { useEffect, useState } from 'preact/hooks'
import './app.css'
import {
  ApiError,
  fetchCategories,
  fetchMe,
  type AuthUser,
  type Category,
  type StudySession,
} from './api'
import { Building } from './building'
import { Decks } from './decks'
import { DifficultyStep } from './difficulty'
import { Login } from './login'
import { navigate, parsePath, pathFor, type Route } from './routes'
import { Study } from './study'

function readRoute(): Route {
  return parsePath(window.location.pathname)
}

function difficultiesMatch(
  a: StudySession['difficulties'],
  b: StudySession['difficulties'],
): boolean {
  if (a.length !== b.length) return false
  return a.every((item, index) => item === b[index])
}

export function App() {
  const [authReady, setAuthReady] = useState(false)
  const [user, setUser] = useState<AuthUser | null>(null)
  const [bootError, setBootError] = useState<string | null>(null)
  const [route, setRoute] = useState<Route>(readRoute)
  const [categories, setCategories] = useState<Category[] | null>(null)
  const [categoriesError, setCategoriesError] = useState<string | null>(null)
  const [session, setSession] = useState<StudySession | null>(null)

  useEffect(() => {
    function onPopState() {
      setRoute(readRoute())
    }
    window.addEventListener('popstate', onPopState)
    return () => window.removeEventListener('popstate', onPopState)
  }, [])

  useEffect(() => {
    // Normalize unknown/malformed paths to their resolved route.
    const canonical = pathFor(route)
    if (canonical !== window.location.pathname) {
      window.history.replaceState(null, '', canonical)
    }
  }, [route])

  useEffect(() => {
    let cancelled = false

    async function boot() {
      try {
        const me = await fetchMe()
        if (cancelled) return
        if (me.authenticated) {
          setUser(me)
        } else {
          setUser(null)
        }
      } catch (err) {
        if (cancelled) return
        if (err instanceof ApiError && err.status === 401) {
          setUser(null)
          return
        }
        setBootError(err instanceof Error ? err.message : 'Failed to reach API')
        setUser(null)
      } finally {
        if (!cancelled) setAuthReady(true)
      }
    }

    void boot()
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    if (!user) {
      setCategories(null)
      return
    }

    let cancelled = false

    async function loadCategories() {
      try {
        const rows = await fetchCategories()
        if (!cancelled) {
          setCategories(rows)
          setCategoriesError(null)
        }
      } catch (err) {
        if (cancelled) return
        if (err instanceof ApiError && err.status === 401) {
          setUser(null)
          return
        }
        setCategoriesError('Could not load decks. Try again.')
        setCategories([])
      }
    }

    void loadCategories()
    return () => {
      cancelled = true
    }
  }, [user])

  useEffect(() => {
    // Drop a stale in-memory session when the URL no longer matches it.
    if (!session) return
    if (route.name !== 'session') {
      setSession(null)
      return
    }
    if (
      session.category.id !== route.categoryId ||
      !difficultiesMatch(session.difficulties, route.difficulties)
    ) {
      setSession(null)
    }
  }, [route, session])

  useEffect(() => {
    if (!categories || route.name === 'home') return
    const found = categories.find((row) => row.id === route.categoryId)
    if (!found) {
      navigate({ name: 'home' }, { replace: true })
    }
  }, [categories, route])

  function go(next: Route, options?: { replace?: boolean }) {
    navigate(next, options)
  }

  function onSignedOut() {
    setUser(null)
    setCategories(null)
    setSession(null)
    go({ name: 'home' }, { replace: true })
  }

  if (!authReady) {
    return (
      <main class="app">
        <p class="building-status">Loading…</p>
      </main>
    )
  }

  if (!user) {
    return (
      <Login
        bootError={bootError}
        onSuccess={(next) => {
          setBootError(null)
          setUser(next)
        }}
      />
    )
  }

  const category =
    route.name === 'home'
      ? null
      : (categories?.find((row) => row.id === route.categoryId) ?? null)

  if (route.name === 'session-new') {
    if (categories === null) {
      return (
        <main class="app">
          <p class="building-status">Loading…</p>
        </main>
      )
    }
    if (!category) {
      return (
        <main class="app">
          <p class="building-status">Loading…</p>
        </main>
      )
    }
    return (
      <DifficultyStep
        category={category}
        onBack={() => go({ name: 'home' })}
        onContinue={(difficulties) =>
          go({ name: 'session', categoryId: category.id, difficulties })
        }
      />
    )
  }

  if (route.name === 'session') {
    if (categories === null || !category) {
      return (
        <main class="app">
          <p class="building-status">Loading…</p>
        </main>
      )
    }

    if (
      session &&
      session.category.id === route.categoryId &&
      difficultiesMatch(session.difficulties, route.difficulties)
    ) {
      return <Study session={session} onExit={() => go({ name: 'home' })} />
    }

    return (
      <Building
        category={category}
        difficulties={route.difficulties}
        onReady={setSession}
        onCancel={() =>
          go({ name: 'session-new', categoryId: category.id }, { replace: true })
        }
      />
    )
  }

  return (
    <Decks
      user={user}
      categories={categories}
      categoriesError={categoriesError}
      onSignedOut={onSignedOut}
      onSelectCategory={(next) =>
        go({ name: 'session-new', categoryId: next.id })
      }
    />
  )
}
