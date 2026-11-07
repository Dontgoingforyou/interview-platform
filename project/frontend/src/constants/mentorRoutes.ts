/**
 * Префиксы путей SPA для роли mentor: совместимо с MENTOR_ALLOWED_* на бэкенде.
 */
export const MENTOR_ALLOWED_ROUTE_PREFIXES = [
  '/interviews-database',
  '/auth',
  '/login',
  '/no-access',
] as const

export const MENTOR_DEFAULT_PATH = '/interviews-database'

/** Проверка pathname после basename (например /interviews-database). */
export function isMentorAllowedPath(pathname: string): boolean {
  if (pathname === '/' || pathname === '') {
    return false
  }
  return MENTOR_ALLOWED_ROUTE_PREFIXES.some(
    (p) => pathname === p || pathname.startsWith(`${p}/`),
  )
}
