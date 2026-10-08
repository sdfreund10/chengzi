export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

function getCookie(name: string): string | null {
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`))
  return match ? decodeURIComponent(match[1]) : null
}

export type AuthUser = {
  authenticated: true
  email: string
}

export type AuthState =
  | AuthUser
  | {
      authenticated: false
      email: null
    }

type RequestOptions = {
  method?: string
  body?: unknown
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const method = options.method ?? 'GET'
  const headers: Record<string, string> = {
    Accept: 'application/json',
  }

  if (options.body !== undefined) {
    headers['Content-Type'] = 'application/json'
  }

  if (method !== 'GET' && method !== 'HEAD') {
    const csrf = getCookie('csrftoken')
    if (csrf) {
      headers['X-CSRFToken'] = csrf
    }
  }

  const response = await fetch(path, {
    method,
    headers,
    credentials: 'same-origin',
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  })

  if (!response.ok) {
    let message = 'Request failed'
    try {
      const data = (await response.json()) as { detail?: string }
      if (typeof data.detail === 'string') {
        message = data.detail
      }
    } catch {
      // ignore non-JSON error bodies
    }
    throw new ApiError(response.status, message)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return (await response.json()) as T
}

export function fetchMe(): Promise<AuthState> {
  return apiRequest<AuthState>('/api/auth/me/')
}

export function login(email: string, password: string): Promise<AuthUser> {
  return apiRequest<AuthUser>('/api/auth/login/', {
    method: 'POST',
    body: { email, password },
  })
}

export function logout(): Promise<AuthState> {
  return apiRequest<AuthState>('/api/auth/logout/', { method: 'POST' })
}
