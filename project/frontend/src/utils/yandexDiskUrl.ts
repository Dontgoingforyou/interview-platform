/**
 * Согласовано с interviews.models.is_yandex_disk_public_file_url:
 * публичная ссылка на файл/папку Яндекс.Диска / Яндекс 360.
 */
const YANDEX_DISK_PUBLIC_HOSTS = new Set([
  'disk.yandex.ru',
  'disk.yandex.com',
  'disk.yandex.kz',
  'yadi.sk',
  'disk.360.yandex.ru',
])

export function isYandexDiskPublicFileUrl(url: string | null | undefined): boolean {
  if (!url || typeof url !== 'string') {
    return false
  }
  const s = url.trim()
  const lower = s.toLowerCase()
  if (!lower.startsWith('http://') && !lower.startsWith('https://')) {
    return false
  }
  let parsed: URL
  try {
    parsed = new URL(s)
  } catch {
    return false
  }
  const host = (parsed.hostname || '').toLowerCase()
  if (!YANDEX_DISK_PUBLIC_HOSTS.has(host) && !host.endsWith('.disk.yandex.ru')) {
    return false
  }
  const path = parsed.pathname.replace(/^\/+|\/+$/g, '')
  if (!path) {
    return false
  }
  const first = path.split('/', 1)[0].toLowerCase()
  if (first === 'client' || first === 'showcaptcha') {
    return false
  }
  return true
}
