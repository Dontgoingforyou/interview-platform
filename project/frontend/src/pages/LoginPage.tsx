import { useEffect, useState, type FormEvent } from 'react'
import { Navigate, useSearchParams } from 'react-router-dom'

import { loginWithPassword } from '../api/authApi'
import { isDevBypassAuth } from '../constants/devAuth'
import { SESSION_ACCESS_TOKEN } from '../constants/sessionAuth'
import { useAuthStore } from '../store/authStore'

const DEMO_ACCOUNTS = [
  { login: 'admin', password: 'demo-admin' },
  { login: 'manager', password: 'demo-manager' },
  { login: 'student', password: 'demo-student' },
] as const

function LoginPage() {
  const [params] = useSearchParams()
  const next = params.get('next') || ''
  const bypass = isDevBypassAuth()
  const user = useAuthStore((s) => s.user)
  const accessToken = useAuthStore((s) => s.accessToken)
  const setSession = useAuthStore((s) => s.setSession)
  const clearSession = useAuthStore((s) => s.clearSession)
  const [username, setUsername] = useState('admin')
  const [password, setPassword] = useState('')
  const [message, setMessage] = useState('')

  const safeNext = next.startsWith('/') && !next.startsWith('//') && !next.startsWith('/login') ? next : ''

  useEffect(() => {
    if (bypass || accessToken || !user) {
      return
    }
    // Старая запись: пользователь есть, токена нет. Уход на /interviews
    // сразу возвращает сюда, и вкладка зависает на пустом экране.
    clearSession()
    useAuthStore.persist.clearStorage()
  }, [accessToken, bypass, clearSession, user])

  if (bypass) {
    const to = next && next.startsWith('/') && !next.startsWith('//') ? next : '/interviews'
    return <Navigate to={to} replace />
  }

  if (user && accessToken) {
    return <Navigate to={safeNext || '/interviews'} replace />
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setMessage('')
    try {
      const data = await loginWithPassword(username, password)
      setSession({
        access_token: SESSION_ACCESS_TOKEN,
        expires_in: data.expires_in,
        user: data.user,
      })
      const target = safeNext || data.redirect_after_login || '/interviews'
      window.location.assign(target)
    } catch {
      setMessage('Неверный логин или пароль')
    }
  }

  return (
    <main className="login-page">
      <form onSubmit={onSubmit} className="login-card">
        <h1>Вход</h1>
        <label className="login-field">
          Логин
          <input
            name="username"
            autoComplete="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
        </label>
        <label className="login-field">
          Пароль
          <input
            name="password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </label>
        {message ? <p className="login-error">{message}</p> : null}
        <button type="submit" className="btn btn-primary">Войти</button>
        <div className="login-demo">
          <p className="login-demo-title">Демо</p>
          <ul>
            {DEMO_ACCOUNTS.map((account) => (
              <li key={account.login}>
                {account.login}
                {' / '}
                {account.password}
              </li>
            ))}
          </ul>
        </div>
      </form>
    </main>
  )
}

export default LoginPage
