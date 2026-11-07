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
    version: '1.0.8',
    date: '2026-11-07',
    text: 'В справке менеджеров роли описаны как заранее заданные демо-учётки.',
  },
  {
    version: '1.0.7',
    date: '2026-11-07',
    text: 'Из справки базы знаний убрана общая фраза про коллег и команду.',
  },
  {
    version: '1.0.6',
    date: '2026-11-07',
    text: 'Из долгов убрана колонка статуса бота. Резервная таблица больше не выгружается и не показывается в списке собеседований.',
  },
  {
    version: '1.0.5',
    date: '2026-11-07',
    text: 'В справке больше нет названия компании, корпоративного бота и резервной таблицы как обычной кнопки.',
  },
  {
    version: '1.0.4',
    date: '2026-11-07',
    text: 'Окно входа одно: и прямой адрес, и кнопка «Выйти» открывают страницу портала.',
  },
  {
    version: '1.0.3',
    date: '2026-11-07',
    text: 'На странице входа каждый демо-пользователь на своей строке. Из меню убрана ссылка на Telegram.',
  },
  {
    version: '1.0.2',
    date: '2026-11-07',
    text: 'Страница входа больше не остаётся пустой, если в браузере осталась старая сессия без токена.',
  },
  {
    version: '1.0.1',
    date: '2026-11-07',
    text: 'Из портала убраны корпоративный Telegram, пароли HH и внешний RAG. Справка и экран «нет доступа» описывают локальные демо-роли.',
  },
  {
    version: '1.0.0',
    date: '2026-11-07',
    text: 'Локальный вход вместо внешнего SSO. Демо-роли: администратор, менеджер и студент.',
  },
  {
    version: '0.9.0',
    date: '2026-11-01',
    text: 'Платформа собеседований: стажёры, собеседования, офферы и журнал «Что нового».',
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
