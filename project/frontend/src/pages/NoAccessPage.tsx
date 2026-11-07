import { Navigate } from 'react-router-dom'

import { isDevBypassAuth } from '../constants/devAuth'
import { KEYCLOAK_ROLE_NO_ACCESS } from '../constants/keycloakRoles'
import { useAuthStore } from '../store/authStore'
import { isPureStudentPortalUser } from '../utils/authRoles'

/**
 * Пользователь вошёл, но ни одна демо-группа не даёт доступа к приложению.
 * Вне MainLayout: без бокового меню менеджера/студента.
 */
function NoAccessPage() {
  const user = useAuthStore((s) => s.user)
  const accessToken = useAuthStore((s) => s.accessToken)
  const clearSession = useAuthStore((s) => s.clearSession)

  if (isDevBypassAuth()) {
    return <Navigate to="/interviews" replace />
  }

  if (!accessToken || !user) {
    return <Navigate to="/login" replace />
  }

  if (user.manager_role !== KEYCLOAK_ROLE_NO_ACCESS) {
    const to = isPureStudentPortalUser(user) ? '/interns-portal' : '/interviews'
    return <Navigate to={to} replace />
  }

  function handleLogout() {
    clearSession()
    window.location.href = '/accounts/logout/'
  }

  return (
    <div
      className="page-wrapper"
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '1.5rem',
      }}
    >
      <main
        style={{
          maxWidth: '32rem',
          lineHeight: 1.55,
        }}
      >
        <h1 style={{ fontSize: '1.35rem', marginBottom: '0.75rem' }}>Нет доступа</h1>
        <p style={{ marginBottom: '1rem', color: 'var(--text-secondary, #666)' }}>
          Для этой учётной записи не назначена роль, с которой можно работать в платформе.
        </p>
        <p style={{ marginBottom: '1.25rem', color: 'var(--text-secondary, #666)' }}>
          Обратитесь к администратору, чтобы вам выдали нужную группу.
        </p>
        <button type="button" className="btn-logout" onClick={handleLogout}>
          Выйти
        </button>
      </main>
    </div>
  )
}

export default NoAccessPage
