/** Строит URL профиля Telegram по username (с @ или без). */
export function internTelegramHref(username: string | null): string | null {
  if (!username) {
    return null
  }
  const u = username.replace(/^@/, '')
  return `https://t.me/${u}`
}
