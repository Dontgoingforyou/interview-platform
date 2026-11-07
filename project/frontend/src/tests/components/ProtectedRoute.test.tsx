/**
 * Доступ по сессии и ролям: редирект на /login, ограничение admin-only, HR на запрещённый путь.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { Route, Routes } from 'react-router-dom'
import { render, screen } from '@testing-library/react'

import ProtectedRoute from '../../components/ProtectedRoute'
import type { AuthUser } from '../../store/authStore'
import { TestProviders } from '../testUtils'

const authState = vi.hoisted(() => ({
  accessToken: null as string | null,
  user: null as AuthUser | null,
}))

vi.mock('../../store/authStore', () => ({
  useAuthStore: (selector: (s: { accessToken: string | null; user: AuthUser | null }) => unknown) =>
    selector({
      accessToken: authState.accessToken,
      user: authState.user,
    }),
}))

function baseUser(overrides: Partial<AuthUser> = {}): AuthUser {
  return {
    email: 'u@test',
    username: 'user',
    full_name: 'Пользователь',
    manager_role: 'manager',
    groups: ['employment'],
    ...overrides,
  }
}

function renderWithAppRoutes(initialEntries: string[]) {
  return render(
    <TestProviders initialEntries={initialEntries}>
      <Routes>
        <Route path="/login" element={<div data-testid="login-page">Вход</div>} />
        <Route path="/no-access" element={<div data-testid="no-access-page">Нет доступа</div>} />
        <Route path="/interviews" element={<div data-testid="interviews-page">Собеседования</div>} />
        <Route
          path="/interviews-database"
          element={<div data-testid="interviews-database-page">База собеседований</div>}
        />
        <Route
          path="/debts"
          element={
            <ProtectedRoute>
              <div data-testid="debts-page">Долги</div>
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin-only"
          element={
            <ProtectedRoute roles={['admin']}>
              <div data-testid="admin-only">Только админ</div>
            </ProtectedRoute>
          }
        />
      </Routes>
    </TestProviders>,
  )
}

describe('ProtectedRoute', () => {
  beforeEach(() => {
    authState.accessToken = null
    authState.user = null
  })

  it('без токена редиректит на страницу входа', () => {
    renderWithAppRoutes(['/debts'])
    expect(screen.getByTestId('login-page')).toBeInTheDocument()
    expect(screen.queryByTestId('debts-page')).not.toBeInTheDocument()
  })

  it('без пользователя редиректит на вход', () => {
    authState.accessToken = 'token'
    authState.user = null
    renderWithAppRoutes(['/debts'])
    expect(screen.getByTestId('login-page')).toBeInTheDocument()
  })

  it('пускает менеджера на защищённый маршрут', () => {
    authState.accessToken = 'token'
    authState.user = baseUser()
    renderWithAppRoutes(['/debts'])
    expect(screen.getByTestId('debts-page')).toBeInTheDocument()
  })

  it('менеджера с маршрута только для admin перенаправляет на /interviews', () => {
    authState.accessToken = 'token'
    authState.user = baseUser({ manager_role: 'manager' })
    renderWithAppRoutes(['/admin-only'])
    expect(screen.getByTestId('interviews-page')).toBeInTheDocument()
    expect(screen.queryByTestId('admin-only')).not.toBeInTheDocument()
  })

  it('админ проходит на маршрут с roles admin', () => {
    authState.accessToken = 'token'
    authState.user = baseUser({ manager_role: 'admin', groups: ['admin', 'employment'] })
    renderWithAppRoutes(['/admin-only'])
    expect(screen.getByTestId('admin-only')).toBeInTheDocument()
  })

  it('HR на запрещённый раздел перенаправляет на /interviews', () => {
    authState.accessToken = 'token'
    authState.user = baseUser({ manager_role: 'hr', groups: ['hrs'] })
    renderWithAppRoutes(['/debts'])
    expect(screen.getByTestId('interviews-page')).toBeInTheDocument()
    expect(screen.queryByTestId('debts-page')).not.toBeInTheDocument()
  })

  it('ментор на запрещённый раздел перенаправляет на /interviews-database', () => {
    authState.accessToken = 'token'
    authState.user = baseUser({ manager_role: 'mentor', groups: ['mentors'] })
    renderWithAppRoutes(['/debts'])
    expect(screen.getByTestId('interviews-database-page')).toBeInTheDocument()
    expect(screen.queryByTestId('debts-page')).not.toBeInTheDocument()
  })

  it('роль no_access перенаправляет на /no-access', () => {
    authState.accessToken = 'token'
    authState.user = baseUser({ manager_role: 'no_access', groups: [] })
    renderWithAppRoutes(['/debts'])
    expect(screen.getByTestId('no-access-page')).toBeInTheDocument()
    expect(screen.queryByTestId('debts-page')).not.toBeInTheDocument()
  })
})
