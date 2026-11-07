/**
 * Префиксы путей SPA (относительно basename корня сайта): совместимо с
 * HR_ALLOWED_REACT_PATH_PREFIXES и HR_OUTSTAFF_ALLOWED_* на бэкенде.
 */
export const HR_ALLOWED_ROUTE_PREFIXES = [
  '/interviews',
  '/interviews-database',
  '/directions',
  '/sad-intern',
  '/developers',
  '/interns',
  '/companies',
  '/managers',
  '/employees',
  '/auth',
  '/login',
  '/no-access',
] as const

/** Разделы и формы, недоступные HR/outstaff (как HR_OUTSTAFF_ALLOWED_URL_NAMES на Django). */
const HR_FORBIDDEN_PATH_PREFIXES = [
  '/knowledge-base',
  '/debts',
  '/offers',
  '/help',
  '/employees/admin',
  '/interns-portal',
] as const

function isHrOutstaffForbiddenPath(pathname: string): boolean {
  for (const p of HR_FORBIDDEN_PATH_PREFIXES) {
    if (pathname === p || pathname.startsWith(`${p}/`)) {
      return true
    }
  }
  if (pathname === '/interns/new') {
    return true
  }
  if (/^\/interns\/\d+\/edit$/.test(pathname)) {
    return true
  }
  if (pathname === '/interviews/new') {
    return true
  }
  if (/^\/interviews\/\d+\/edit$/.test(pathname)) {
    return true
  }
  if (/^\/interviews\/\d+\/duplicate$/.test(pathname)) {
    return true
  }
  return false
}

/** Проверка pathname после basename (например /interviews). */
export function isHrAllowedPath(pathname: string): boolean {
  if (pathname === '/' || pathname === '') {
    return true
  }
  if (isHrOutstaffForbiddenPath(pathname)) {
    return false
  }
  return HR_ALLOWED_ROUTE_PREFIXES.some((p) => pathname === p || pathname.startsWith(`${p}/`))
}
