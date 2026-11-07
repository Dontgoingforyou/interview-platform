/**
 * Абсолютный URL документной страницы Django (не React Router).
 * В production обычно тот же origin; в dev — Vite proxy /debts или VITE_DJANGO_ORIGIN.
 */
export function getDjangoDocumentUrl(path: string): string {
  const normalized = path.startsWith('/') ? path : `/${path}`
  if (import.meta.env.PROD) {
    return normalized
  }
  const origin = import.meta.env.VITE_DJANGO_ORIGIN?.replace(/\/$/, '')
  if (origin) {
    return `${origin}${normalized}`
  }
  return normalized
}
