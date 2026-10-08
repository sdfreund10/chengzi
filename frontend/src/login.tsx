import { useState } from 'preact/hooks'
import { ApiError, login, type AuthUser } from './api'

type LoginProps = {
  onSuccess: (user: AuthUser) => void
  bootError?: string | null
}

export function Login({ onSuccess, bootError = null }: LoginProps) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function onSubmit(event: Event) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      const user = await login(email.trim(), password)
      onSuccess(user)
    } catch (err) {
      if (err instanceof ApiError && err.status === 400) {
        setError(err.message)
      } else {
        setError('Could not sign in. Try again.')
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main class="app">
      <header>
        <p class="eyebrow">juzi</p>
        <h1>Sign in</h1>
        <p class="lede">Session login for your study account.</p>
      </header>

      <section class="panel">
        <form class="login-form" onSubmit={onSubmit}>
          <label>
            <span>Email</span>
            <input
              type="email"
              name="email"
              autocomplete="username"
              required
              value={email}
              onInput={(e) => setEmail((e.target as HTMLInputElement).value)}
            />
          </label>
          <label>
            <span>Password</span>
            <input
              type="password"
              name="password"
              autocomplete="current-password"
              required
              value={password}
              onInput={(e) => setPassword((e.target as HTMLInputElement).value)}
            />
          </label>
          {(error || bootError) && <p class="error">{error ?? bootError}</p>}
          <button type="submit" disabled={submitting}>
            {submitting ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
      </section>
    </main>
  )
}
