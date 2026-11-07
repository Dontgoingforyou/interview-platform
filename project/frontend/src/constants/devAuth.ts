/**
 * Обход формы входа только в dev при VITE_DEV_BYPASS_AUTH=true.
 * Обычный запуск использует локальные демо-учётки на странице /login.
 */
import type { AuthUser } from '../store/authStore'

/** Маркер токена: не отправлять как Bearer в API (см. api/client.ts). */
export const DEV_BYPASS_ACCESS_TOKEN = '__DEV_BYPASS__'

export type DevMockRole = 'admin' | 'hr' | 'manager' | 'mentor'

export function isDevBypassAuth(): boolean {
  return (
    import.meta.env.DEV &&
    import.meta.env.VITE_DEV_BYPASS_AUTH === 'true' &&
    import.meta.env.PROD === false
  )
}

function parseMockRole(): DevMockRole {
  const raw = import.meta.env.VITE_DEV_MOCK_ROLE
  if (raw === 'admin' || raw === 'hr' || raw === 'manager' || raw === 'mentor') {
    return raw
  }
  return 'admin'
}

/** Фиктивный пользователь для Navbar и ProtectedRoute. */
export function getDevMockUser(): AuthUser {
  const role = parseMockRole()
  const groups: string[] =
    role === 'hr'
      ? ['hrs']
      : role === 'mentor'
        ? ['mentors']
        : role === 'admin'
          ? ['admin', 'employment']
          : ['employment']

  return {
    email: 'dev@local.invalid',
    username: 'dev_user',
    full_name: 'Режим разработки',
    manager_role:
      role === 'hr'
        ? 'hr'
        : role === 'mentor'
          ? 'mentor'
          : role === 'admin'
            ? 'admin'
            : 'manager',
    groups,
  }
}
