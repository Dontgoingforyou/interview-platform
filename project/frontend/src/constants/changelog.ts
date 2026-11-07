export const CHANGELOG_SEEN_VERSION_KEY = 'interview-management-changelog-seen-version'

export const WHATS_NEW_PAGE_SIZE = 10

export const WHATS_NEW_EMPTY_TEXT = 'Пока нет заметных обновлений'

export type WhatsNewEntry = {
  version: string
  date: string
  text: string
}

const MONTHS_RU = [
  'января',
  'февраля',
  'марта',
  'апреля',
  'мая',
  'июня',
  'июля',
  'августа',
  'сентября',
  'октября',
  'ноября',
  'декабря',
] as const

/** Записи от новых к старым. Порядок задан явно: строковая сортировка «1.1.10» и «1.1.9» врёт. */
export const WHATS_NEW_ENTRIES: readonly WhatsNewEntry[] = [
  {
    version: '1.0.1',
    date: '2026-11-07',
    text: 'Из портала убраны корпоративные данные: Telegram компании, пароли HH и внешний RAG.',
  },
]

export function changelogSeenStorageKey(username: string): string {
  return `${CHANGELOG_SEEN_VERSION_KEY}:${username}`
}

export function hasUnseenWhatsNew(seenVersion: string | null, latestVersion: string | null): boolean {
  if (latestVersion == null || latestVersion === '') {
    return false
  }
  return seenVersion !== latestVersion
}

export function whatsNewPage(entries: readonly WhatsNewEntry[], pageIndex: number): WhatsNewEntry[] {
  if (pageIndex < 0) {
    return []
  }
  const start = pageIndex * WHATS_NEW_PAGE_SIZE
  return entries.slice(start, start + WHATS_NEW_PAGE_SIZE)
}

export function formatWhatsNewDate(isoDate: string): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(isoDate)
  if (!match) {
    return isoDate
  }
  const day = Number(match[3])
  const month = MONTHS_RU[Number(match[2]) - 1]
  if (!month || day < 1 || day > 31) {
    return isoDate
  }
  return `${day} ${month}`
}
