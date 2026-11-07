/**
 * Чтение куки для заголовка X-CSRFToken (Django CsrfViewMiddleware).
 * Имя по умолчанию — csrftoken (CSRF_COOKIE_NAME).
 */
export function getCookie(name: string): string | null {
  if (typeof document === 'undefined') {
    return null
  }
  const escaped = name.replace(/([.$?*|{}()[\]\\/+^])/g, '\\$1')
  const match = document.cookie.match(new RegExp(`(?:^|; )${escaped}=([^;]*)`))
  return match ? decodeURIComponent(match[1]) : null
}
