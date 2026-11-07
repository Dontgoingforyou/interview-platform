import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { useAuthStore } from '../../store/authStore'
import { isPureStudentPortalUser } from '../../utils/authRoles'

const STUDENT_ALLOWED_PATHS = new Set(['/interns-portal'])

/**
 * Для «чистого» студента разрешён только портал (зеркало StudentRedirectMiddleware для SPA).
 */
function StudentPortalAccess() {
  const user = useAuthStore((s) => s.user)
  const location = useLocation()

  if (!isPureStudentPortalUser(user)) {
    return <Outlet />
  }

  if (!STUDENT_ALLOWED_PATHS.has(location.pathname)) {
    return <Navigate to="/interns-portal" replace />
  }

  return <Outlet />
}

export default StudentPortalAccess
