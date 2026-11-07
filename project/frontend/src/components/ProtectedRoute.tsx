import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'

import { KEYCLOAK_ROLE_NO_ACCESS } from '../constants/keycloakRoles'
import { isHrAllowedPath } from '../constants/hrRoutes'
import { isMentorAllowedPath, MENTOR_DEFAULT_PATH } from '../constants/mentorRoutes'
import { useAuthStore } from '../store/authStore'

interface ProtectedRouteProps {
  children: ReactNode
  /** Если задано — доступ только при одной из ролей сессии */
  roles?: string[]
}

function ProtectedRoute({ children, roles }: ProtectedRouteProps) {
  const accessToken = useAuthStore((s) => s.accessToken)
  const user = useAuthStore((s) => s.user)
  const location = useLocation()

  if (!accessToken || !user) {
    return <Navigate to="/login" replace state={{ from: location }} />
  }

  if (user.manager_role === KEYCLOAK_ROLE_NO_ACCESS) {
    return <Navigate to="/no-access" replace />
  }

  if (roles && roles.length > 0 && !roles.includes(user.manager_role)) {
    const fallback =
      user.manager_role === 'mentor' ? MENTOR_DEFAULT_PATH : '/interviews'
    return <Navigate to={fallback} replace />
  }

  if (user.manager_role === 'mentor' && !isMentorAllowedPath(location.pathname)) {
    return <Navigate to={MENTOR_DEFAULT_PATH} replace />
  }

  if (
    (user.manager_role === 'hr' || user.manager_role === 'outstaff') &&
    !isHrAllowedPath(location.pathname)
  ) {
    return <Navigate to="/interviews" replace />
  }

  return children
}

export default ProtectedRoute
