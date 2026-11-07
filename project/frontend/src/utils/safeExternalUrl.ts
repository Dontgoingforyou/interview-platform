/**
 * Безопасные внешние ссылки: блокирует javascript:, data: и прочие опасные схемы.
 */

const BLOCKED_SCHEMES = /^(javascript|data|vbscript|file):/i

export function safeExternalUrl(raw: string | null | undefined): string | null {
  if (raw == null) {
    return null
  }
  const trimmed = String(raw).trim()
  if (!trimmed) {
    return null
  }
  if (BLOCKED_SCHEMES.test(trimmed)) {
    return null
  }
  if (trimmed.startsWith('//')) {
    return null
  }
  try {
    const url = new URL(trimmed, window.location.origin)
    if (url.protocol === 'http:' || url.protocol === 'https:') {
      return url.href
    }
  } catch {
    return null
  }
  return null
}
